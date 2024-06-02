# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

# Configuration file for JupyterHub
import os
import shutil
c = get_config()  # noqa: F821

# We rely on environment variables to configure JupyterHub so that we
# avoid having to rebuild the JupyterHub container every time we change a
# configuration parameter.

# Spawn single-user servers as Docker containers
#c.JupyterHub.spawner_class = "dockerspawner.DockerSpawner"

from dockerspawner import DockerSpawner

class CustomDockerSpawner(DockerSpawner):
    def start(self):
        #self.environment['CUDA_VISIBLE_DEVICES'] = '0'
        
        # 필요한 경우 다른 환경 설정
        self.extra_host_config = {
            'runtime': 'nvidia',
            'device_requests': [
                {'capabilities': [['gpu']],
                 'count': 1
                }  # 첫 번째 GPU만 할당
            ]
        }
        self.environment['CUDA_VISIBLE_DEVICES'] = '0'
        return super().start()


# Configure the JupyterHub to use the custom spawner
c.JupyterHub.spawner_class = CustomDockerSpawner

# Spawn containers from this image
c.DockerSpawner.image = os.environ["DOCKER_NOTEBOOK_IMAGE"]
# Connect containers to this Docker network
network_name = os.environ["DOCKER_NETWORK_NAME"]
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.network_name = network_name

# Explicitly set notebook directory because we'll be mounting a volume to it.
# Most `jupyter/docker-stacks` *-notebook images run the Notebook server as
# user `jovyan`, and set the notebook directory to `/home/jovyan/work`.
# We follow the same convention.
notebook_dir = os.environ.get("DOCKER_NOTEBOOK_DIR", "/home/jovyan/work")
c.DockerSpawner.notebook_dir = notebook_dir

def create_dir_hook(spawner):
    username = spawner.user.name # get the username
    volume_path = os.path.join('/home/', username) #path on the jupytherhub host, create a folder based on username if not exists
    if not os.path.exists(volume_path):
        os.mkdir(volume_path)
        shutil.chown(volume_path, user=username, group='users')
c.Spawner.pre_spawn_hook = create_dir_hook


# Mount the real user's Docker volume on the host to the notebook user's
# notebook directory in the container
c.DockerSpawner.volumes = {"jupyterhub-user-{username}": notebook_dir}

# Remove containers once they are stopped
c.DockerSpawner.remove = True

#c.DockerSpawner.extra_host_config = {'runtime': 'nvidia'}
#c.DockerSpawner.extra_host_config = {'runtime': 'nvidia', 'device_requests': [docker.types.DeviceRequest(count=-1, capabilities=[['gpu']])]}
c.DockerSpawner.extra_host_config = {'runtime': 'nvidia', 'privileged': True}
# For debugging arguments passed to spawned containers
c.DockerSpawner.debug = True

# User containers will access hub by container name on the Docker network
c.JupyterHub.hub_ip = "jupyterhub"
c.JupyterHub.hub_port = 8080

# Persist hub data on volume mounted inside container
c.JupyterHub.cookie_secret_file = "/data/jupyterhub_cookie_secret"
c.JupyterHub.db_url = "sqlite:////data/jupyterhub.sqlite"

# Authenticate users with Native Authenticator
c.JupyterHub.authenticator_class = "nativeauthenticator.NativeAuthenticator"

# Allow anyone to sign-up without approval
c.NativeAuthenticator.open_signup = True

c.Authenticator.admin_users = {'cocopam'}
c.Authenticator.allow_all = True
# Allowed admins
admin = os.environ.get("JUPYTERHUB_ADMIN")
if admin:
    c.Authenticator.admin_users = [admin]
