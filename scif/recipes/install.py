'''

Copyright (C) 2017 The Board of Trustees of the Leland Stanford Junior
University.
Copyright (C) 2017 Vanessa Sochat.

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public
License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

'''


from scif.logger import bot
from scif.utils import ( mkdir_p, run_command, write_file, write_json )
from scif.recipes.helpers import get_parts
import sys
import os


def install(self, app=None):
    '''install recipes to a base. We assume this is the root of a system
       or container, and will write the /scif directory on top of it.
       If an app name is provided, install that app if it is found 
       in the config. This function goes through all step to:

       1. Install base folders to base, creating a folder for each app
       2. Install one or more apps to it, the config is already loaded
    '''

    self._install_base()             # Generate the folder structure
    self._install_apps(app)          # App install


def init_app(self, app):
    '''initialize an app, meaning adding the metadata folder, bin, and 
       lib to it. The app is created at the base
    '''
    settings = get_appenv(app, self._base)[app]

    # Create base directories for metadata
    for folder in ['appmeta', 'appbin', 'applib', 'appdata']:
        mkdir_p(settings[folder])
    return settings


def install_app(self, apps=None):
    '''install one or more apps to the base. If app is defined, only
       install app specified. Otherwise, install all found in config.
    '''
    if apps is None:
        apps = self.apps()

    if not isinstance(apps, list):
        apps = [apps]

    for app in apps:

        # We must have the app defined in the config
        if app not in self._config['apps']:
            bot.error('Cannot find app %s in config.' %app)
            sys.exit(1)

        # Make directories
        settings = self._init_app(app)

        # Get the app configuration
        config = self.app(app)

        # Handle environment, runscript, labels
        self._install_runscript(app, settings, config)
        self._install_environment(app, settings, config)
        self._install_labels(app, settings, config)
        self._install_commands(app, settings, config)
        self._install_files(app, settings, config)
        self._install_recipe(app, settings, settings, config)


def install_runscript(self, app, settings, config):
    '''install runscript will prepare the runscript for an app.
       
       Parameters
       ==========
       app should be the name of the app, for lookup in config['apps']
       settings: the output of _init_app(), a dictionary of environment vars
       config: should be the config for the app obtained with self.app(app)

    '''
    if "apprun" in config:
        content = '\n'.join(config['runscript'])
        bot.info('+ ' + 'apprun '.ljust(5) + app)
        write_file(settings['apprun'], content)


def install_labels(self, app, settings, config):
    '''install labels will add labels to the app labelfile

       Parameters
       ==========
       app should be the name of the app, for lookup in config['apps']
       settings: the output of _init_app(), a dictionary of environment vars
       config: should be the config for the app obtained with self.app(app)

    '''
    lookup = dict()
    if "applabels" in config:
        labels = config['appfiles']
        bot.info('+ ' + 'applabels '.ljust(5) + app)
        for line in labels:
            label, value = get_parts(pair, default='')
            lookup[label] = value
 
        write_json(settings['applabels'], lookup)
    return lookup


def install_files(self, app, settings, config):
    '''install files will add files (or directories) to a destination.
       If none specified, they are placed in the app base

       Parameters
       ==========
       app should be the name of the app, for lookup in config['apps']
       settings: the output of _init_app(), a dictionary of environment vars
       config: should be the config for the app obtained with self.app(app)

    '''
    files = []
    if "appfiles" in config:
        files = config['appfiles']
        bot.info('+ ' + 'appfiles '.ljust(5) + app)

        for pair in files:

            # Step 1: determine source and destination
            src, dest = get_parts(pair, default=settings['approot'])

            # Step 2: copy source to destination
            cmd = ['cp']

            if os.path.isdir(src):
                cmd.append('-R')

            cmd.append(dest)
            result = self._run_command(cmd)
            files.append(dest)

    return files

def install_commands(self, app, settings, config):
    '''install will finally, issue commands to install the app.

       Parameters
       ==========
       app should be the name of the app, for lookup in config['apps']
       settings: the output of _init_app(), a dictionary of environment vars
       config: should be the config for the app obtained with self.app(app)

    '''
    if "appinstall" in config:
        cmd = config['appinstall']
        bot.info('+ ' + 'appinstall '.ljust(5) + app)
        return self._run_command(cmd)


def install_recipe(self, app, settings, config):
    '''Write the initial recipe for the app to its metadata folder.

       Parameters
       ==========
       app should be the name of the app, for lookup in config['apps']
       settings: the output of _init_app(), a dictionary of environment vars
       config: should be the config for the app obtained with self.app(app)

    '''
    recipe_file = settings['apprecipe']
    recipe = '' 

    for section_name, section_content in config.items():
        content = '\n'.join(content)
        header = '%' + section_name
        recipe += '%s %s\n%s\n' %(header, app, content)

    write_file(recipe_file, recipe)
    return recipe

            
def install_environment(self, app, settings, config):
    '''install will prepare the global runscript, if defined

       Parameters
       ==========
       app should be the name of the app, for lookup in config['apps']
       settings: the output of _init_app(), a dictionary of environment vars

    '''
    if "appenv" in config:
        cmd = config['install']
        bot.info('+ ' + 'apprun '.ljust(5) + app)
        return self._run_command(cmd)