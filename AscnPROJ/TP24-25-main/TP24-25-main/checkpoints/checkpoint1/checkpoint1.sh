#!/bin/bash

###################################################################
#Script Name	: checkpoint1.sh
#Description	: This script is used to test Checkpoint 1
#Args           : -i <path-to-code-folder> -o <path-to-results-folder>
#Author       	: ASCN Team
###################################################################


################################
# Clean up the environment     #
################################
function clean_up {
    echo "> Cleaning up..."
    docker kill moonshot moonshotdb > /dev/null 2>&1
    docker rm moonshot moonshotdb > /dev/null 2>&1
    docker network rm moonshot_net > /dev/null 2>&1
    docker rmi moonshot > /dev/null 2>&1
}


################################
# Setup the environment        #
################################
function setup {
    echo "> Setting up"
    LOGS=$1
    mkdir -p $LOGS

    clean_up
}

################################
# Log message to file(s)       #
################################
function log_msg {
    MSG="$1"
    LOG_FILE="$2"

    echo -e -n "$MSG" >> "$LOG_FILE"

    if [ -n "$3" ]
    then
        echo -e "$MSG" >> "$3"
    fi

}

################################
# Check directory structure    #
################################
function check_structure {
    echo "> Checking directory structure"
    TEST_PATH="$1"
    LOGS="$2"
    LOG_FILE="$LOGS/checkpoint1.log"

    log_msg "[Task-1] Checking directory structure..." "$LOG_FILE"
    if [ ! -d "$TEST_PATH" ]
    then
        echo -e " FAILED! Directory 'docker' not found!" >> "$LOG_FILE" 2>&1
        return 1
    else
        echo -e " OK!" >> "$LOG_FILE" 2>&1
    fi
    return 0
}

################################
# Build Moonshot image         #
################################
function build_moonshot_image {
    echo "> Building image"
    TEST_PATH="$1"
    LOGS="$2"
    LOG_FILE="$LOGS/checkpoint1.log"
    TASK_LOG="$LOGS/task-2.log"

    # Enter Docker directory
    cd $TEST_PATH > /dev/null 2>&1

    # Clean cache
    sudo sh -c 'echo 3 >/proc/sys/vm/drop_caches' > /dev/null 2>&1

    # Build image
    log_msg "[Task-2] Building Moonshot image..." "$LOG_FILE" "$TASK_LOG"
    timeout 800 docker build --no-cache --rm -t moonshot . >> "$TASK_LOG" 2>&1
    if [ $? -eq 0 ]
    then
        echo -e " OK!"  >> "$LOG_FILE" 2>&1
    else
        echo -e " FAILED! Check task-2.log for more information."  >> "$LOG_FILE" 2>&1
        return 2
    fi

    return 0
}

################################
# Run DB container             #
################################
function run_db_container {
    echo "> Running DB container..."
    LOGS="$1"
    LOG_FILE="$LOGS/checkpoint1.log"
    TASK_LOG="$LOGS/task-3.log"

    # Create network
    log_msg "[Task-3] Creating Docker network..." "$LOG_FILE" "$TASK_LOG"
    docker network create moonshot_net >> "$TASK_LOG" 2>&1
    if [ $? -eq 0 ]
    then
        echo -e " OK!" >> "$LOG_FILE" 2>&1
    else
        echo -e " FAILED! Check task-3.log for more information." >> "$LOG_FILE" 2>&1
        return 1
    fi

    # Run Postgres container
    log_msg "[Task-3] Starting Postgres container ..." "$LOG_FILE" "$TASK_LOG"
    docker run --name moonshotdb --net moonshot_net -p 5432:5432 -e  POSTGRES_USER=admin -e POSTGRES_PASSWORD=password -e POSTGRES_DB=moonshot -d postgres:15.4 >> $TASK_LOG 2>&1
    if [ $? -eq 0 ]
    then
        echo -e " OK!"  >> $LOG_FILE 2>&1
    else
        docker logs moonshotdb > $LOGS/db-logs.txt 2>&1
        echo -e " FAILED! Check task-3.log and db-logs.txt for more information."  >> $LOG_FILE 2>&1
        return 1
    fi

    # Wait for Postgres to be ready
    log_msg "[Task-3] Waiting for Postgres to be ready..." "$LOG_FILE" "$TASK_LOG"
    timeout 90s bash -c "until docker exec moonshotdb pg_isready ; do sleep 5 ; done" >> $TASK_LOG 2>&1
    if [ $? -eq 0 ]
    then
        echo -e " OK!"  >> $LOG_FILE 2>&1
    else
        echo -e " FAILED!"  >> $LOG_FILE 2>&1
        return 1
    fi

    return 0
}

################################
# Run Moonshot container       #
################################
function run_moonshot_container {
    echo "> Running Moonshot container..."
    LOGS="$1"
    LOG_FILE="$LOGS/checkpoint1.log"
    TASK_LOG="$LOGS/task-4.log"

    # Run Moonshot container
    log_msg "[Task-4] Starting Moonshot container..." "$LOG_FILE" "$TASK_LOG"
    docker run --name moonshot --net moonshot_net -p 8000:8000 -e DB_USER=admin -e DB_PASSWORD=password -e DB_NAME=moonshot -e DB_HOST=moonshotdb -e DB_PORT=5432 -d moonshot  >> $TASK_LOG 2>&1
    if [ $? -eq 0 ]
    then
        echo -e " OK!"  >> $LOG_FILE 2>&1
    else
        docker logs moonshot > $LOGS/moonshot-logs.txt 2>&1
        echo -e "FAILED! Check task-4.log and moonshot-logs.txt for more information."  >> $LOG_FILE 2>&1
        return 1
    fi

    sleep 5s

    log_msg "[Task-4] Check if Moonshot container is still running..." "$LOG_FILE" "$TASK_LOG"
    if [ "$(docker inspect -f '{{.State.Running}}' moonshot)" = "true" ]
    then
        echo -e " OK!"  >> $LOG_FILE 2>&1
    else
        echo -e " FAILED! Moonshot container is not running!"  >> $LOG_FILE 2>&1
        return 1
    fi


    return 0
}

################################
# Test Moonshot access         #
################################
function test_moonshot_access {
    echo "> Testing Moonshot access..."
    LOGS="$1"
    LOG_FILE="$LOGS/checkpoint1.log"
    TASK_LOG="$LOGS/task-5.log"

    # Test Moonshot access
    log_msg "[Task-5] Checking access to Moonshot..." "$LOG_FILE" "$TASK_LOG"s
    RETRY_CURL=true
    RETRIES=1
    while [ "$RETRY_CURL" = true ]
    do
        status_code=$(curl --silent --output "$LOGS/output.html" --write-out '%{http_code}' http://localhost:8000/api/health)
        if [[ "$status_code" -eq 200 ]] ;
        then
            echo -e " OK!"  >> $LOG_FILE 2>&1
            echo -e "\n\t - OK! Moonshot is accessible!"  >> $LOG_FILE 2>&1
            RETRY_CURL=false
        else
            echo -e "\n\t - FAILED! Moonshot is not accessible! Retrying in 5 seconds..."  >> $TASK_LOG 2>&1
            sleep 5
            RETRIES=$((RETRIES+1))
            if [ $RETRIES -gt 5 ]
            then
                echo -e "\n\t - FAILED! Moonshot is not accessible after 5 retries!"  >> $TASK_LOG 2>&1
                echo -e " FAILED! Check task-5.log, moonshot-logs.txt and output.html files for more information."  >> $LOG_FILE 2>&1
                docker logs moonshot > $LOGS/moonshot-logs.txt 2>&1
                return 1
            fi
        fi
    done

    return 0
}


################################
# Main function                #
################################
function main {
    echo "Running Checkpoint 1 for \"$1\""
    CUR_PATH=$(pwd)

    case $2 in
        /*) LOGS_FOLDER=$2 ;;
        *) LOGS_FOLDER="$CUR_PATH/$2" ;;
    esac

    echo "Logs will be saved in \"$LOGS_FOLDER\""
    setup "$LOGS_FOLDER"

    check_structure "$1/docker" "$LOGS_FOLDER"
    if [ $? -ne 0 ]
    then
        clean_up
        echo "Task 1 failed! Check $LOGS_FOLDER/checkpoint1.log for more information."
        return 1
    fi

    build_moonshot_image "$1/docker" "$LOGS_FOLDER"
    if [ $? -ne 0 ]
    then
        clean_up
        echo "Task 2 failed! Check $LOGS_FOLDER/checkpoint1.log for more information."
        return 2
    fi

    run_db_container "$LOGS_FOLDER"
    if [ $? -ne 0 ]
    then
        clean_up
        echo "Task 3 failed! Check $LOGS_FOLDER/checkpoint1.log for more information."
        return 3
    fi

    run_moonshot_container "$LOGS_FOLDER"
    if [ $? -ne 0 ]
    then
        clean_up
        echo "Task 4 failed! Check $LOGS_FOLDER/checkpoint1.log for more information."
        return 4
    fi

    test_moonshot_access "$LOGS_FOLDER"
    if [ $? -ne 0 ]
    then
        clean_up
        echo "Task 5 failed! Check $LOGS_FOLDER/checkpoint1.log for more information."
        return 5
    fi

    clean_up

    echo "Tasks completed successfully! Check $LOGS_FOLDER/checkpoint1.log for more information."
    return 0
}


#########################
# The command line help #
#########################
display_help() {
    echo "Usage: $0 -i <path-to-code-folder> -o <path-to-results-folder>" >&2
    echo
    echo "   -i, --input           Code directory path to test"
    echo "   -o, --output          Output directory path to save logs"
    echo
    exit 1
}

################################
# Check if parameters options  #
# are given on the commandline #
################################
input=""
output=""
while :
do
    case "$1" in
      -i | --input)
          if [ $# -ne 0 ]; then
            input="$2"   # You may want to check validity of $2
          fi
          shift 2
          ;;
      -o | --output)
          if [ $# -ne 0 ]; then
            output="$2"   # You may want to check validity of $2
          fi
          shift 2
          ;;
      -h | --help)
          display_help  # Call your function
          exit 0
          ;;
      *)  # No more options
          break
          ;;
    esac
done


################################
# Check if parameters are empty#
################################
if [ -z "$input" ] || [ -z "$output" ]; then
    display_help
    exit 1
fi

################################
# Call the main function       #
################################
main "$input" "$output"