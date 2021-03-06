#!/usr/bin/env python
# -*- coding: utf-8 -*-
import flask
import time
import os
import json
import subprocess

# Директория с deps2.0 для сервисов
services_dir_env = 'services/'
# Укажите абсолютный путь к корневой директории сервиса!
ROOT = '/vagrant/web-deps/'
SERVICE_DIR_ENV_ABS = ROOT + services_dir_env

# Кол-во послених сборок отображаемых в вэб интерфейсе
count_string = 15


web_deps = flask.Flask(__name__, static_folder=ROOT)

@web_deps.route('/')
@web_deps.route('/<path:path>')
def send_static(path = False):
    # Здесь мы посылаем всю статику клиенту - html, js скрипты, css стили
    print 'Requested file path: {0}'.format(path)

    if not path:
            return web_deps.send_static_file('index.html')

    return web_deps.send_static_file(path)



def list_services(services_dir,n):
    sorted_release_folder = [dirs for dirs in os.listdir(services_dir) if os.path.isdir(os.path.join(services_dir, dirs))] # Отображает только директории
    sorted_release_folder.sort()
    return sorted_release_folder[-n:]


@web_deps.route("/ping")
def ping():
   return "pong"

@web_deps.route("/list_s") # Отображает список директорий в services_dir_env
def list_s():
    return flask.jsonify(services=list_services(services_dir_env,0))


@web_deps.route("/list_r") #Отображает список версий релизов из подпапки releases. Требует параметр service_dir.
def list_r():
    service_dir = flask.request.args.to_dict()['service_dir']
    return flask.jsonify(service_dir=service_dir, releases=list_services(services_dir_env + service_dir + '/releases/', count_string))

@web_deps.route("/list_serverstodeploy") #Отображает список серверов куда можно выложить данный релиз. Список серверов указывается в файле .serverstodeploy
def list_std():
    service_dir = flask.request.args.to_dict()['service_dir']
    file = open(SERVICE_DIR_ENV_ABS + service_dir + '/.serverstodeploy', 'r')
    ln_std = file.readlines()
    file.close()
    ln_std = map(lambda s: s.strip(), ln_std)
    if os.path.exists(SERVICE_DIR_ENV_ABS + service_dir + '/.lastrelease'):
        os.remove(SERVICE_DIR_ENV_ABS + service_dir + '/.lastrelease')
    for line in ln_std:
        cmd = 'cd ' + SERVICE_DIR_ENV_ABS + service_dir + ' && fab check_release_version -H ' + line
        a=subprocess.Popen([cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        a.communicate()
    file = open(SERVICE_DIR_ENV_ABS + service_dir + '/.lastrelease', 'r')
    ln_lr = file.readlines()
    file.close()
    ln_lr = map(lambda s: s.strip(), ln_lr)
    return flask.jsonify(serverstodeploy=zip(ln_std, ln_lr))


@web_deps.route('/web-deps_int')
def web_deps_int():
    service_dir = flask.request.args.to_dict()['service_dir']
    release_dir = flask.request.args.to_dict()['release_dir']
    servers_to_deploy = flask.request.args.to_dict()['servers_to_deploy']
    cmd = 'cd ' + SERVICE_DIR_ENV_ABS + service_dir + ' && fab web-do:release=' + release_dir + ' -H ' + servers_to_deploy
    def inner():
        proc = subprocess.Popen(
            [cmd],             #call something with a lot of output so we can see it
            shell=True,
            stdout=subprocess.PIPE
#            stderr=subprocess.PIPE
        )
        #stdout,stderror=proc.communicate()
        for line in iter(proc.stdout.readline,''):
            time.sleep(1)                           # Don't need this just shows the text streaming
            yield line.rstrip() + '<br/>'

    response = flask.Response(inner(), mimetype='text/html')
    response.headers.add('X-Accel-Buffering', 'no')
    return response


if __name__ == "__main__":
   web_deps.run(host='0.0.0.0')
