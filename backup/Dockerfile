FROM docker:27-cli
# bash + curl + GNU coreutils (split -d) + tzdata для локального расписания
RUN apk add --no-cache bash curl coreutils tzdata
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
