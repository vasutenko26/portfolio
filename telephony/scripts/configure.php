<?php
/**
 * Configure a typical small-office PBX scenario on the demo FreePBX stand:
 *   - 4 PJSIP extensions (101 Reception, 102 Sales, 103 Support, 104 Manager)
 *   - System recording for the IVR greeting
 *   - Support call queue (2001) with recording forced ON
 *   - IVR "Main Menu": 1 -> Sales (ext 102), 2 -> Support queue (2001)
 *   - Time Group + Time Condition "Office Hours" (Mon-Fri 09:00-18:00)
 *
 * Run inside the freepbx container:  php /tmp/configure.php
 * Idempotent-ish: removes objects with the same id/name before re-adding.
 */

$bootstrap_settings['freepbx_auth'] = false;
include '/etc/freepbx.conf';
$FreePBX = FreePBX::create();
global $db, $amp_conf, $astman;

// FreePBX installs a strict Whoops handler that escalates PHP warnings (e.g.
// undefined-array-key in optional settings) to fatals. Restore plain handling
// so optional/defaulted keys don't abort this batch script.
restore_error_handler();
restore_exception_handler();
error_reporting(E_ERROR | E_PARSE);

function pout($m){ echo $m . "\n"; }

/* ----------------------------------------------------------------- *
 * 1) Extensions
 * ----------------------------------------------------------------- */
$exts = array(
  array('101','Reception'),
  array('102','Sales'),
  array('103','Support'),
  array('104','Manager'),
);
foreach ($exts as $e) {
  list($num,$nm) = $e;
  // clean slate (also clears any half-created device from a prior aborted run)
  @$FreePBX->Core->delDevice($num);
  @$FreePBX->Core->delUser($num);
  $res = $FreePBX->Core->processQuickCreate('pjsip', $num, array(
    'name'   => $nm,
    'secret' => bin2hex(random_bytes(9)),
  ));
  $ok = (is_array($res) && isset($res['status'])) ? $res['status'] : $res;
  pout("ext $num ($nm): " . json_encode($res));
}

/* ----------------------------------------------------------------- *
 * 2) System recording (IVR greeting)
 * ----------------------------------------------------------------- */
$recId = null;
foreach ($FreePBX->Recordings->getAllRecordings() as $r) {
  if ($r['displayname'] === 'office-greeting') { $recId = $r['id']; }
}
if (!$recId) {
  $recId = $FreePBX->Recordings->addRecording('office-greeting','Main office IVR greeting','custom/office-greeting');
}
pout("recording office-greeting id = $recId");

/* ----------------------------------------------------------------- *
 * 3) Support queue 2001 (recording forced ON)
 *    queues_add() reads most settings from $_REQUEST — populate it.
 * ----------------------------------------------------------------- */
require_once($amp_conf['AMPWEBROOT'].'/admin/modules/queues/functions.inc.php');

$_REQUEST = array_merge($_REQUEST, array(
  'maxlen'             => '0',
  'joinempty'          => 'yes',
  'leavewhenempty'     => 'no',
  'strategy'           => 'ringall',
  'timeout'            => '15',
  'retry'              => '5',
  'wrapuptime'         => '0',
  'announcefreq'       => '0',
  'min-announce'       => '15',
  'announceholdtime'   => 'no',
  'announceposition'   => 'no',
  'pannouncefreq'      => '0',
  'recording'          => 'always',   // <-- force call recording on this queue
  'weight'             => '0',
  'autofill'           => '1',
  'reportholdtime'     => 'no',
  'autopause'          => 'no',
  'autopausedelay'     => '0',
  'servicelevel'       => '60',
  'memberdelay'        => '0',
  'timeoutrestart'     => 'no',
  'timeoutpriority'    => 'app',
  'penaltymemberslimit'=> '0',
  'rtone'              => '0',
  'music'              => 'default',
  'maxwait'            => '300',
));

if (function_exists('queues_del')) { @queues_del('2001'); }

// members: real support agents (PJSIP) + a self-contained auto-answer agent
// (Local/s@demo-agent) so the local proof-call connects and records a conversation.
$members = array('PJSIP/103,0', 'PJSIP/104,1', 'Local/s@demo-agent,0');

queues_add(
  '2001',                      // account
  'Support',                   // name
  '',                          // password
  '',                          // prefix
  'app-blackhole,hangup,1',    // goto (failover after max wait)
  '',                          // agentannounce_id
  $members,                    // members
  '',                          // joinannounce_id
  '300',                       // maxwait
  '',                          // alertinfo
  '0',                         // cwignore
  '',                          // qregex
  '0',                         // queuewait
  '0',                         // use_queue_context
  array(),                     // dynmembers (must be array — used by array_unique)
  'no',                        // dynmemberonly
  '0',                         // togglehint
  '0',                         // qnoanswer
  '0',                         // callconfirm
  '',                          // callconfirm_id
  'mixmon',                    // monitor_type
  '0',                         // monitor_heard
  '0',                         // monitor_spoken
  '0',                         // answered_elsewhere
  'always'                     // recording
);
pout("queue 2001 (Support) created with members: " . implode(' ', $members));

/* ----------------------------------------------------------------- *
 * 4) IVR "Main Menu"
 * ----------------------------------------------------------------- */
// remove an existing IVR with the same name
foreach ($FreePBX->Ivr->getDetails() as $iv) {
  if (isset($iv['name']) && $iv['name'] === 'Main Menu') {
    $FreePBX->Ivr->delete($iv['id']);
  }
}
$ivrVals = array(
  'name'                 => 'Main Menu',
  'description'          => 'Office main menu — 1 Sales, 2 Support',
  'announcement'         => $recId,
  'directdial'           => 'all',
  'invalid_loops'        => '3',
  'invalid_retry_recording' => 'default',
  'invalid_recording'    => 'default',
  'invalid_destination'  => 'from-did-direct,101,1',
  'timeout_enabled'      => '1',
  'timeout_time'         => '10',
  'timeout_recording'    => 'default',
  'timeout_retry_recording' => 'default',
  'timeout_destination'  => 'from-did-direct,101,1',
  'timeout_loops'        => '3',
  'retvm'                => 'off',
);
$FreePBX->Ivr->saveDetail($ivrVals);
// fetch the new id
$ivrId = null;
foreach ($FreePBX->Ivr->getDetails() as $iv) {
  if ($iv['name'] === 'Main Menu') { $ivrId = $iv['id']; }
}
pout("IVR 'Main Menu' id = $ivrId");

$entries = array(
  array('ivr_id'=>$ivrId, 'selection'=>'1', 'dest'=>'from-did-direct,102,1', 'ivr_ret'=>0), // Sales
  array('ivr_id'=>$ivrId, 'selection'=>'2', 'dest'=>'ext-queues,2001,1',     'ivr_ret'=>0), // Support queue
);
$FreePBX->Ivr->saveEntry($ivrId, $entries);
pout("IVR entries: 1 -> Sales (102), 2 -> Support queue (2001)");

/* ----------------------------------------------------------------- *
 * 5) Time Group + Time Condition "Office Hours" (Mon-Fri 09:00-18:00)
 * ----------------------------------------------------------------- */
// drop existing TC + TG with same name
$db->query("DELETE FROM timeconditions WHERE displayname = 'Office Hours'");
foreach ($FreePBX->Timeconditions->listTimegroups() as $tg) {
  if ($tg['description'] === 'Office Hours') { $FreePBX->Timeconditions->delTimeGroup($tg['id']); }
}
$times = array(array(
  'hour_start'=>'09','minute_start'=>'00','hour_finish'=>'18','minute_finish'=>'00',
  'wday_start'=>'mon','wday_finish'=>'fri',
  'mday_start'=>'-','mday_finish'=>'-','month_start'=>'-','month_finish'=>'-',
));
$tgId = $FreePBX->Timeconditions->addTimeGroup('Office Hours', $times);
pout("time group 'Office Hours' id = $tgId");

$pdo = $FreePBX->Database;
$stmt = $pdo->prepare("INSERT INTO timeconditions (displayname,time,truegoto,falsegoto,deptname,generate_hint,fcc_password,invert_hint,timezone,mode) VALUES (?,?,?,?,?,1,?,0,?,?)");
$stmt->execute(array(
  'Office Hours',
  $tgId,
  'ivr-'.$ivrId.',s,1',          // within hours -> IVR
  'app-blackhole,hangup,1',      // outside hours -> hang up (closed)
  '', '', '', 'time-group',
));
$tcId = $pdo->lastInsertId();
pout("time condition 'Office Hours' id = $tcId -> true=IVR($ivrId), false=hangup");

pout("=== CONFIG DONE ===");
