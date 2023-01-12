FROM node:16 as builder 

COPY package.json package-lock.json / 
RUN npm ci 

COPY src/ /src/ 
COPY webpack.config.js / 
RUN npm run build

FROM docker.io/ubuntu:20.04

RUN apt update -y && DEBIAN_FRONTEND=noninteractive apt install -y python3-pip tzdata libmariadb-dev
RUN pip install django

COPY . /app
RUN mkdir /db

WORKDIR /app
RUN pip install -r requirements.txt
COPY --from=builder /dist /app/dist 

CMD /bin/sh /app/entrypoint.sh
