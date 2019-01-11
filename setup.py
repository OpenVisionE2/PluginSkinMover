from distutils.core import setup
import setup_translate

pkg = 'Extensions.PluginSkinMover'
setup (name = 'enigma2-plugin-extensions-pluginskinmover',
       version = '0.6',
       description = 'Move plugins and skins between flash memory and pen drive',
       packages = [pkg],
       package_dir = {pkg: 'plugin'},
       package_data = {pkg: ['plugin.png', '*/*.png', 'locale/*/LC_MESSAGES/*.mo']},
       cmdclass = setup_translate.cmdclass, # for translation
      )
