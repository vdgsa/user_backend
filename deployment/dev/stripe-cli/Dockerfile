# # From https://github.com/stripe/stripe-cli?tab=readme-ov-file#docker

FROM  stripe/stripe-cli
RUN  apk  add  pass  gpg-agent
COPY  ./entrypoint.sh  /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT  [ "/entrypoint.sh" ]
