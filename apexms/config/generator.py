import os
from typing import Dict, List
from .parsers import Configuration, Database, Service



class GitGenerator:
    def __init__(self, config:Configuration, base_path:str):
        self.config = config
        self.base_path = base_path

    def generate(self):
        pass


class ProjectGenerator:
    def __init__(self, name:str, service:Service, base_path:str):
        self.name = name
        self.service = service
        self.project_path = os.path.join(base_path, name)
        os.makedirs(self.project_path, exist_ok=True)
        print(f"Generating project {name} at {self.project_path}")

    def generate(self):
        self.generate_env()
        self.generate_wait_for_it()
        self.generate_entrypoint()
        self.generate_dockerfile()

    def generate_dockerfile(self):
        with open(os.path.join(self.project_path, 'Dockerfile'), 'w') as f:
            f.write("FROM python:3.11.9\n\n")
            f.write("ENV PYTHONUNBUFFERED 1\n\n")
            f.write("WORKDIR /app\n\n")
            f.write("COPY requirements.txt .\n\n")
            f.write("RUN pip install --no-cache-dir -r requirements.txt\n\n")
            f.write("COPY . /app/\n\n")
            f.write(f"EXPOSE {self.service.port}\n\n")
            f.write("RUN chmod +x /app/wait-for-it.sh\n")
            f.write("RUN chmod +x /app/entrypoint.sh\n\n")
            f.write("ENTRYPOINT [\"/app/entrypoint.sh\"]\n")

    def generate_env(self):
        """
        group all env variables from service and databases
        by preifix of the service name
        """
        env_vars:Dict[str, List[str]] = {}
        for env in self.service.environments:
            prefix = env.split('=')[0].split('_')[0]
            if prefix not in env_vars:
                env_vars[prefix] = [env]
            else:
                env_vars[prefix].append(env)

        with open(os.path.join(self.project_path, '.env'), 'w') as f:
            for prefix, env_list in env_vars.items():
                f.write(f"#{prefix.capitalize()} environment variables\n")
                for env in env_list:
                    f.write(env + '\n')
                f.write('\n')
 
    def generate_requirements(self):
        pass

    def generate_venv(self):
        pass

    def generate_project(self):
        project_generators = {
            'django': self.generate_django,
            'flask': self.generate_flask,
            'fastapi': self.generate_fastapi
        }
        project_generators[self.service.framework]()

    def generate_django(self):
        pass

    def generate_flask(self):
        pass

    def generate_fastapi(self):
        pass

    def generate_wait_for_it(self):
        entry_point = """
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
        with open(os.path.join(self.project_path, 'wait-for-it.sh'), 'w') as f:
            f.write(entry_point)

    def generate_entrypoint(self):
        """
        #!/bin/bash

        echo "Waiting for RabbitMQ to start..."
        ./wait-for-it.sh rabbitmq:5672 --strict -t 30

        echo "Waiting for Redis Server to start..."
        ./wait-for-it.sh redis:6379 --strict -t 30

        echo "Waiting for Postgres Post-Write Database to start..."
        ./wait-for-it.sh posts-write-db:5432 --strict -t 30

        echo "Making Migrations..."
        python manage.py makemigrations

        echo "Migrating the Database..."
        python manage.py migrate

        echo "Starting the server..."
        python manage.py runserver 0.0.0.0:8000 &

        echo "Starting RabbitMQ Consumer..."
        python consumers.py &

        echo "Starting Celery..."
        celery -A postwrite worker --loglevel=info &

        echo "Starting Celery Beat..."
        celery -A postwrite beat --loglevel=info

        exec "$@"
        """
        with open(os.path.join(self.project_path, 'entrypoint.sh'), 'w') as f:
            f.write("#!/bin/bash\n\n")

            for db_name, db in self.service.database_list.items():
                f.write(f"echo \"Waiting for {db_name} to start...\"\n")
                for port in db.ports:
                    f.write(f"./wait-for-it.sh {db_name}:{port.split(':')[-1]} --strict -t 30\n")
            f.write("\n")
            if self.service.framework == 'django':
                f.write("echo \"Making Migrations...\"\n")
                f.write("python manage.py makemigrations\n\n")
                f.write("echo \"Migrating the Database...\"\n")
                f.write("python manage.py migrate\n\n")
                f.write("echo \"Starting the server...\"\n")
                f.write(f"python manage.py runserver 0.0.0.0:{self.service.port}")

            elif self.service.framework == 'flask':
                f.write("echo \"Starting the server...\"\n")
                f.write(f"python app.py")

            elif self.service.framework == 'fastapi':
                f.write("echo \"Starting the server...\"\n")
                f.write(f"fastapi run dev")

            f.write("\n\nexec \"$@\"\n")
            


class ServiceGenerator:
    def __init__(self, services:Dict[str, Service], base_path:str):
        self.services = services
        self.base_path = base_path

    def generate(self):
        for name, service in self.services.items():
            project_generator = ProjectGenerator(name, service, self.base_path)
            project_generator.generate()


class DatabaseGenerator:
    def __init__(self, databases:Dict[str, Database], base_path:str):
        self.databases = databases
        self.base_path = base_path

    def generate(self):
        pass


class Generator:
    def __init__(self, config:Configuration, base_path:str):
        project_name = os.path.join(base_path, config.metadata.project)
        os.makedirs(project_name, exist_ok=True)
        self.service_generator = ServiceGenerator(config.services, project_name)
        self.git_generator = GitGenerator(config, project_name)

    def generate(self):
        self.service_generator.generate()
        self.git_generator.generate()