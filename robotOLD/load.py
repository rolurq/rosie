# -*- coding: utf-8 -*-
import importlib
import os
import logging


from settings import config as global_settings


__all__ = ['SETTINGS', 'load_global_settings']

#### IMPORT ####


SETTINGS = None


def load_global_settings():
    """
    Load the robotOLD's profile defined in the global settings.
    """
    global SETTINGS
    profile = global_settings.get('general', 'profile')
    if os.path.exists(os.path.join(os.getcwd(), 'profiles', profile)):
        try:
            # substitute dirty exec call
            SETTINGS = importlib.import_module("profiles.%s.settings" %
                                               (profile))
            logging.info('loaded profile: ' + profile)
        except:
            SETTINGS = None
            logging.error("error loading profile <"+profile+">")
    else:
        logging.warning("directory <"+profile+"> does not exist")
