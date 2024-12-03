import os
import sys
import yaml

class GenerateProject:
    def __init__(self, service, path: str):
        self.service = service
        self.path = path
        self.generate()
    
    def generate(self):
        if self.service.framework == "django":
            self.generate_django()
        elif self.service.framework == "flask":
            self.generate_flask()
        elif self.service.framework == "fastapi":
            self.generate_fastapi()

    def generate_django(self):
        # activate virtual environment and check operating system
        if sys.platform == "win32":
            os.system(f"{self.path}/venv/Scripts/activate")
        else:
            os.system(f"source {self.path}/venv/bin/activate")
        # create project using django-admin
        os.system(f"django-admin startproject {self.service.name} {self.path}")
    
    def generate_flask(self):
        script = "from flask import Flask\n"
        script += "\n"
        script += "app = Flask(__name__)\n"
        script += "\n"
        script += "@app.route('/')\n"
        script += "def hello_world():\n"
        script += "\treturn 'Hello, World!'\n"
        script += "\n"
        script += "\n"
        script += "if __name__ == '__main__':\n"
        script += "\timport uvicorn\n"
        script += f"\tuvicorn.run(app, host='0.0.0.0', port={self.service.port})\n"

        with open(os.path.join(self.path, "app.py"), 'w') as f:
            f.write(script)

    def generate_fastapi(self):
        script = "from fastapi import FastAPI\n"
        script += "\n"
        script += "app = FastAPI()\n"
        script += "\n"
        script += "@app.get('/')\n"
        script += "def read_root():\n"
        script += "\treturn {'Hello': 'World'}\n"

        with open(os.path.join(self.path, "app.py"), 'w') as f:
            f.write(script)


class GenerateService:
    def __init__(self, service, path: str):
        self.service = service
        self.path = path

    def generate(self):
        service_path = os.path.join(self.path, self.service.name)
        os.makedirs(service_path, exist_ok=True)
        self.generate_dockerfile()
        self.generate_env()
        self.generate_wait_for_it()
        self.generate_entrypoint()
        self.generate_python_env()
        os.system("deactivate")
        GenerateProject(self.service, service_path)
    
    def generate_dockerfile(self):
        service_path = os.path.join(self.path, self.service.name)
        with open(os.path.join(service_path, "Dockerfile"), 'w') as f:
            f.write(f"FROM {self.service.image}\n")
            f.write("ENV PYTHONUNBUFFERED 1\n")
            f.write("WORKDIR /app\n")
            f.write("COPY requirements.txt .\n")
            f.write("RUN pip install --no-cache-dir -r requirements.txt\n")
            f.write("COPY . /app/\n")
            f.write(f"EXPOSE {self.service.port}\n")
            f.write("RUN chmod +x /app/wait-for-it.sh\n")
            f.write("RUN chmod +x /app/entrypoint.sh\n")
            f.write(f'ENTRYPOINT ["/app/entrypoint.sh"]\n')

    def generate_env(self):
        service_path = os.path.join(self.path, self.service.name)
        with open(os.path.join(service_path, ".env"), 'w') as f:
            env_list = list(set(self.service.environments))
            env_dict = {}
            for env in env_list:
                key, value = env.split("=")
                prefix = key.split("_")[0]
                if prefix not in env_dict:
                    env_dict[prefix] = []
                env_dict[prefix].append(env)
            for key, values in env_dict.items():
                f.write(f"# {key} environment variables\n")
                for value in values:
                    f.write(f"{value}\n")
                f.write("\n")

    def generate_entrypoint(self):
        with open(os.path.join(self.path, self.service.name, "entrypoint.sh"), 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("\n")
            
            # if databases in service wait for them to start
            if len(self.service.databases) > 0:
                for db in self.service.databases:
                    f.write(f"echo 'Waiting for {db} Database to start...'\n")
                    f.write(f"./wait-for-it.sh {db}:5432 --strict -t 30\n")
                    f.write("\n")
            
            # if service is django make migrations and migrate
            if self.service.framework == "django":
                f.write("echo 'Making Migrations...'\n")
                f.write("python manage.py makemigrations\n")
                f.write("\n")
                f.write("echo 'Migrating the Database...'\n")
                f.write("python manage.py migrate\n")
                f.write("\n")
            
            # start the server
            f.write(f"echo 'Starting the {self.service.name} server...'\n")
            if self.service.framework == "django":
                f.write(f"python manage.py runserver {self.service.port}")

            elif self.service.framework == "flask":
                f.write(f"python app.py\n")
            
            elif self.service.framework == "fastapi":
                f.write(f"python app.py\n")

            f.write("\n")
            f.write("exec \"$@\"\n")
    
    def generate_wait_for_it(self):
        wait_for_it = """
#!/bin/bash
# Use this script to test if a given TCP host/port are available

WAITFORIT_cmdname=${0##*/}

echoerr() { if [[ $WAITFORIT_QUIET -ne 1 ]]; then echo "$@" 1>&2; fi }

usage()
{
    cat << USAGE >&2
Usage:
    $WAITFORIT_cmdname host:port [-s] [-t timeout] [-- command args]
    -h HOST | --host=HOST       Host or IP under test
    -p PORT | --port=PORT       TCP port under test
                                Alternatively, you specify the host and port as host:port
    -s | --strict               Only execute subcommand if the test succeeds
    -q | --quiet                Don't output any status messages
    -t TIMEOUT | --timeout=TIMEOUT
                                Timeout in seconds, zero for no timeout
    -- COMMAND ARGS             Execute command with args after the test finishes
USAGE
    exit 1
}

wait_for()
{
    if [[ $WAITFORIT_TIMEOUT -gt 0 ]]; then
        echoerr "$WAITFORIT_cmdname: waiting $WAITFORIT_TIMEOUT seconds for $WAITFORIT_HOST:$WAITFORIT_PORT"
    else
        echoerr "$WAITFORIT_cmdname: waiting for $WAITFORIT_HOST:$WAITFORIT_PORT without a timeout"
    fi
    WAITFORIT_start_ts=$(date +%s)
    while :
    do
        if [[ $WAITFORIT_ISBUSY -eq 1 ]]; then
            nc -z $WAITFORIT_HOST $WAITFORIT_PORT
            WAITFORIT_result=$?
        else
            (echo -n > /dev/tcp/$WAITFORIT_HOST/$WAITFORIT_PORT) >/dev/null 2>&1
            WAITFORIT_result=$?
        fi
        if [[ $WAITFORIT_result -eq 0 ]]; then
            WAITFORIT_end_ts=$(date +%s)
            echoerr "$WAITFORIT_cmdname: $WAITFORIT_HOST:$WAITFORIT_PORT is available after $((WAITFORIT_end_ts - WAITFORIT_start_ts)) seconds"
            break
        fi
        sleep 1
    done
    return $WAITFORIT_result
}

wait_for_wrapper()
{
    # In order to support SIGINT during timeout: http://unix.stackexchange.com/a/57692
    if [[ $WAITFORIT_QUIET -eq 1 ]]; then
        timeout $WAITFORIT_BUSYTIMEFLAG $WAITFORIT_TIMEOUT $0 --quiet --child --host=$WAITFORIT_HOST --port=$WAITFORIT_PORT --timeout=$WAITFORIT_TIMEOUT &
    else
        timeout $WAITFORIT_BUSYTIMEFLAG $WAITFORIT_TIMEOUT $0 --child --host=$WAITFORIT_HOST --port=$WAITFORIT_PORT --timeout=$WAITFORIT_TIMEOUT &
    fi
    WAITFORIT_PID=$!
    trap "kill -INT -$WAITFORIT_PID" INT
    wait $WAITFORIT_PID
    WAITFORIT_RESULT=$?
    if [[ $WAITFORIT_RESULT -ne 0 ]]; then
        echoerr "$WAITFORIT_cmdname: timeout occurred after waiting $WAITFORIT_TIMEOUT seconds for $WAITFORIT_HOST:$WAITFORIT_PORT"
    fi
    return $WAITFORIT_RESULT
}

# process arguments
while [[ $# -gt 0 ]]
do
    case "$1" in
        *:* )
        WAITFORIT_hostport=(${1//:/ })
        WAITFORIT_HOST=${WAITFORIT_hostport[0]}
        WAITFORIT_PORT=${WAITFORIT_hostport[1]}
        shift 1
        ;;
        --child)
        WAITFORIT_CHILD=1
        shift 1
        ;;
        -q | --quiet)
        WAITFORIT_QUIET=1
        shift 1
        ;;
        -s | --strict)
        WAITFORIT_STRICT=1
        shift 1
        ;;
        -h)
        WAITFORIT_HOST="$2"
        if [[ $WAITFORIT_HOST == "" ]]; then break; fi
        shift 2
        ;;
        --host=*)
        WAITFORIT_HOST="${1#*=}"
        shift 1
        ;;
        -p)
        WAITFORIT_PORT="$2"
        if [[ $WAITFORIT_PORT == "" ]]; then break; fi
        shift 2
        ;;
        --port=*)
        WAITFORIT_PORT="${1#*=}"
        shift 1
        ;;
        -t)
        WAITFORIT_TIMEOUT="$2"
        if [[ $WAITFORIT_TIMEOUT == "" ]]; then break; fi
        shift 2
        ;;
        --timeout=*)
        WAITFORIT_TIMEOUT="${1#*=}"
        shift 1
        ;;
        --)
        shift
        WAITFORIT_CLI=("$@")
        break
        ;;
        --help)
        usage
        ;;
        *)
        echoerr "Unknown argument: $1"
        usage
        ;;
    esac
done

if [[ "$WAITFORIT_HOST" == "" || "$WAITFORIT_PORT" == "" ]]; then
    echoerr "Error: you need to provide a host and port to test."
    usage
fi

WAITFORIT_TIMEOUT=${WAITFORIT_TIMEOUT:-15}
WAITFORIT_STRICT=${WAITFORIT_STRICT:-0}
WAITFORIT_CHILD=${WAITFORIT_CHILD:-0}
WAITFORIT_QUIET=${WAITFORIT_QUIET:-0}

# Check to see if timeout is from busybox?
WAITFORIT_TIMEOUT_PATH=$(type -p timeout)
WAITFORIT_TIMEOUT_PATH=$(realpath $WAITFORIT_TIMEOUT_PATH 2>/dev/null || readlink -f $WAITFORIT_TIMEOUT_PATH)

WAITFORIT_BUSYTIMEFLAG=""
if [[ $WAITFORIT_TIMEOUT_PATH =~ "busybox" ]]; then
    WAITFORIT_ISBUSY=1
    # Check if busybox timeout uses -t flag
    # (recent Alpine versions don't support -t anymore)
    if timeout &>/dev/stdout | grep -q -e '-t '; then
        WAITFORIT_BUSYTIMEFLAG="-t"
    fi
else
    WAITFORIT_ISBUSY=0
fi

if [[ $WAITFORIT_CHILD -gt 0 ]]; then
    wait_for
    WAITFORIT_RESULT=$?
    exit $WAITFORIT_RESULT
else
    if [[ $WAITFORIT_TIMEOUT -gt 0 ]]; then
        wait_for_wrapper
        WAITFORIT_RESULT=$?
    else
        wait_for
        WAITFORIT_RESULT=$?
    fi
fi

if [[ $WAITFORIT_CLI != "" ]]; then
    if [[ $WAITFORIT_RESULT -ne 0 && $WAITFORIT_STRICT -eq 1 ]]; then
        echoerr "$WAITFORIT_cmdname: strict mode, refusing to execute subprocess"
        exit $WAITFORIT_RESULT
    fi
    exec "${WAITFORIT_CLI[@]}"
else
    exit $WAITFORIT_RESULT
fi
"""
        with open(os.path.join(self.path, self.service.name, "wait-for-it.sh"), 'w') as f:
            f.write(wait_for_it)

    def generate_requirements(self):
        with open(os.path.join(self.path, self.service.name, "requirements.txt"), 'w') as f:
            for req in self.service.requirements:
                f.write(f"{req}\n")

    def install_requirements(self):
        os.system(f"pip install --no-cache-dir -r {self.path}/{self.service.name}/requirements.txt")

    def generate_python_env(self):
        service_path = os.path.join(self.path, self.service.name)
        # genarate python virtual environment
        os.system(f"python -m venv {service_path}/venv")
        # activate the virtual environment
        os.system(f"source {service_path}/venv/bin/activate")
        # install the requirements
        self.install_requirements()
        # generate the requirements.txt
        self.generate_requirements()
        # deactivate the virtual environment


class GenerateDockerCompose:
    def __init__(self, config, path: str):
        self.config = config
        self.path = path
        self.generate()

    def generate(self):

        docker_compose = {
            "services": {},
            "networks": {net:{} for net in list(self.config.networks.networks_list)},
            "volumes": {vol:{} for vol in list(self.config.volumes.volumes_list)}
        }

        for service in self.config.services.values():
            service_dict = {
                "build": {
                    "context": f"./{service.name}",
                    "dockerfile": "Dockerfile"
                },
                "ports": [f"{service.port}:{service.port}"],
                "env_file": [f"{service.name}/.env"],
                "networks": service.networks
            }
            if  len(service.volumes) > 0:
                service_dict['volumes'] = service.volumes
            docker_compose['services'][service.name] = service_dict
        
        with open(os.path.join(self.path, "docker-compose.yaml"), 'w') as f:
            gen_data = yaml.dump(docker_compose, default_flow_style=False, sort_keys=False, indent=4)
            gen_data = gen_data.replace("{}", "")
            f.write(gen_data)