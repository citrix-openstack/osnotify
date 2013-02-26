from setuptools import setup


setup(
    name="osnotify",
    version="0.0",
    packages=["osnotify"],
    entry_points={
        'console_scripts': [
            'osnotify-proxy = osnotify.scripts:proxy',
            'osnotify-subscribe = osnotify.scripts:subscribe',
            'osnotify-publish = osnotify.scripts:publish',
            'osnotify-install-service = osnotify.scripts:install_service'
        ]
    }
)
