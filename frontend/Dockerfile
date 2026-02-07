FROM node:20-alpine

WORKDIR /app

ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ARG http_proxy
ARG https_proxy
ARG no_proxy
ARG NPM_CONFIG_PROXY
ARG NPM_CONFIG_HTTPS_PROXY
ARG NPM_CONFIG_STRICT_SSL

ENV HTTP_PROXY=${HTTP_PROXY} \
    HTTPS_PROXY=${HTTPS_PROXY} \
    NO_PROXY=${NO_PROXY} \
    http_proxy=${http_proxy} \
    https_proxy=${https_proxy} \
    no_proxy=${no_proxy} \
    NPM_CONFIG_PROXY=${NPM_CONFIG_PROXY} \
    NPM_CONFIG_HTTPS_PROXY=${NPM_CONFIG_HTTPS_PROXY} \
    NPM_CONFIG_STRICT_SSL=${NPM_CONFIG_STRICT_SSL}

COPY package.json /app/
RUN npm install

COPY . /app

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
