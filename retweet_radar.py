#!/usr/bin/env python
# coding: utf-8
"""
Documentación de este módulo
"""
import sys
import os
import datetime
import tweepy
import pprint
import ConfigParser
import smtplib
import shelve

try:
    import argparse
except ImportError:
    # argparse no está disponible para Python < 2.7
    # lo ideal sería hacer un fallback a optparse pero por ahora
    # lo mantenemos como una dependencia obligatoria... a no ser que queramos
    # hacer un backport de la librería a versiones menores de la 2.7
    raise


# tupla de tipos de entornos disponibles para la ejecución del programa
VALID_ENVIRONMENTS = ('dev',)


def psa(status_array):
    """Print Status Array (este es el docstring de esta función, accesible
    directamente a través de:
    
        psa.__doc__

    """
    for status in status_array:
        #pprint.pprint(dir(status))
        pprint.pprint(status.retweeted)
    print


def valid_environment(value):
    """Función helper utilizada como callback por argparse para detectar si la
    opción --environment tiene un valor que es aceptado
    """
    if value not in VALID_ENVIRONMENTS:
        msg = "%r no es un entorno soportado" % value
        raise argparse.ArgumentTypeError(msg)
    return value


def valid_path(value):
    """Función helper utilizada como callback por argparse para detectar si la
    opción --config tiene un valor que es aceptado
    """
    if not value:
        value = 'settings.cfg'
    if not os.path.isfile(value):
        msg = "%r no es una ruta al fichero de configuración válida" % value
        raise argparse.ArgumentTypeError(msg)
    return value


def main():
    """Punto de acceso al programa de retweets
    TODO: mover todas las partes de esta función que sean reutilizables a otras
    funciones

    python retweet_radar.py [args]...
    """
    # Parseador de los argumentos pasados al programa, __doc__ es la
    # documentación del módulo
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-e', '--environment', metavar='env', default='dev',
                        type=valid_environment,
                        help='entorno en el que se ejecutará el script, '\
                             'opciones válidas: dev (por defecto), ...')
    parser.add_argument('-v', '--verbosity', default=False, action='store_true',
                        help='mostrar notificaciones en la salida estándard. '\
                             'desactivado por defecto')
    parser.add_argument('-c', '--config', type=valid_path,
                        help='ruta al archivo de configuración, por defecto '\
                             'intenta buscar un archivo `settings.cfg` en el '\
                             'directorio actual')

    args = parser.parse_args()

    environment, verbosity, = args.environment, args.verbosity

    if verbosity:
        print "Running in '%s' MODE" % environment.upper()

    #Configuration for the (ro)bot
    config = ConfigParser.RawConfigParser()
    config.read(args.config)

    # Refactorizar lo siguiente en funciones reutilizables, es decir, desde
    # otros módulos debo ser capaz de importar funcionalidades de este
    #Last retweet
    db = shelve.open(config.get(environment, 'retweeted_history'))
    last_retweet = db['last_retweet']

    #Initialize API and RT flag	
    rt = False
    auth = tweepy.OAuthHandler(config.get(environment, 'consumer_key'), config.get(environment, 'consumer_secret'))
    auth.set_access_token(config.get(environment, 'access_token'), config.get(environment, 'access_token_secret'))
    api = tweepy.API(auth)
    timeline = api.user_timeline(config.get(environment, 'feeder'))
    timeline = reversed(timeline) #from older to newer

    #Open log file and initialize timestamp
    f = open(config.get(environment, 'log_file'), 'a')
    now = datetime.datetime.now()

    #Run over the timeline
    for status in timeline:
            tweet_id = status.id
            tweet_text = status.text
            
            if config.get(environment, 'keyword').lower() in tweet_text.lower() and (tweet_id > last_retweet):
                    rt = True
                    if (environment == 'main'):
                            #api.retweet(tweet_id)
                            optional_via = ' (RT: ' + config.get(environment, 'optional_via') + ')'
                            new_tweet = tweet_text + optional_via
                            total_size = len(new_tweet)
                            my_tweet = new_tweet
                            if (total_size > int(config.get(environment, 'max_tweet_size'))):
                                    my_tweet = tweet_text
                            db['last_retweet'] = tweet_id
                            api.update_status(my_tweet)
                            print 'Status Update: ' + my_tweet
                    else:
                            print config.get(environment, 'got_new_tweet') + ': ' + str(tweet_id)
                    f.write('[' + str(now) +']['+ environment +'] ' + config.get(environment, 'retweeted_log') + ' ' + str(tweet_id) + '\n')
                    print config.get(environment, 'retweeted_print') + ' ' + str(tweet_id)


    if rt:
            print 'Retweets done'
    else:
            f.write('[' + str(now) + ']['+ environment +'] ' + config.get(environment, 'nothing_done_log') + '\n')
            print config.get(environment, 'nothing_done_print')

    f.close()
    db.close()


if __name__ == '__main__':
    # Solo si se ejecuta el módulo directamente y
    # retornar explícitamente un código de error a la shell
    sys.exit(main())
