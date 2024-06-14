#!/usr/bin/env python3

# ./write_terraform.py 41144592 ../service/compute/computeDashboard.tf

# ./write_terraform.py 41145294 ../service/cloudsql/cloudSQLDashboard.tf

# ./write_terraform.py 41144640 ../projectsDashboard.tf

# ./write_terraform.py -d 41144640 -e hagrid-staging -n projectsDashboard.tf -c "/Users/Hagrid/github.com/content-eng-tools/auto-magical-dashboard/config.ini"
# ^ useful for aliasing like so: tfdash="/Users/Hagrid/github.com/content-eng-tools/auto-magical-dashboard/write_terraform.py -e hagrid-staging -c \"/Users/Hagrid/github.com/content-eng-tools/auto-magical-dashboard/config.ini\" -d"
# ^ with this alias, all you type is `tfdash 123456 -n myfancydash.tf` from any terminal

# see https://github.com/observeinc/content-eng-tools/blob/main/engage_datasets/config/configfile.ini for example config file

"""This file is for converting json produced by getTerraform GraphQL method"""

import json
import sys
import os
import configparser
import re
import subprocess
import argparse
import logging
import pathlib

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests
try:
    from gql import gql, Client
    from gql.transport.requests import RequestsHTTPTransport
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "gql"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests-toolbelt"])
    from gql import gql, Client
    from gql.transport.requests import RequestsHTTPTransport


def getObserveConfig(config, environment):
    """Fetches config file"""
    # Set your Observe environment details in config\configfile.ini
    configuration = configparser.ConfigParser()
    configuration.read(args.config_path)
    observe_configuration = configuration[environment]

    return observe_configuration[config]


def get_bearer_token():
    """Gets bearer token for login"""
    url = f"https://{customer_id}.{domain}/v1/login"
    # user_email = getObserveConfig("user_email", ENVIRONMENT)
    # user_password = getObserveConfig("user_password", ENVIRONMENT)

    message = '{"user_email":"$user_email$","user_password":"$user_password$"}'

    tokens_to_replace = {
        "$user_email$": user_email,
        "$user_password$": user_password,
    }

    for key, value in tokens_to_replace.items():
        message = message.replace(key, value)

    header = {
        "Content-Type": "application/json",
    }

    response = json.loads(
        requests.post(url, data=message, headers=header, timeout=10).text
    )
    bear_toke = response["access_key"]
    return bear_toke


def get_ids(file_name):
    """gets unique set of ids that need to be replaced in terraform def"""
    my_list = []
    lines = []
    # read file
    with open(file_name, "r", encoding="utf-8") as fp:
        # read and store all lines into list
        lines = fp.readlines()

    for _, line in enumerate(lines):
        if "datasetId" in line or "keyForDatasetId" in line:
            my_list = my_list + re.findall('"([^"]*)"', line)

    # convert to dict to eliminate duplicate values and then back to list
    my_list = list(dict.fromkeys(my_list))

    return my_list


def get_dashboard_terraform(dashboard_id, output_file_name):
    """get dashboard terraform from graphql"""
    toke = BEARERTOKEN
    # customer_id = getObserveConfig("customer_id", ENVIRONMENT)
    # Create a GraphQL client using the defined transport
    client = Client(
        transport=RequestsHTTPTransport(
            url=META_URL,
            retries=3,
            headers={"Authorization": f"""Bearer {customer_id} {toke}"""},
        ),
        fetch_schema_from_transport=True,
    )

    # Provide a GraphQL query
    query = gql(
        """
          query terraform($dashboard_id: ObjectId!) {
            getTerraform( id:$dashboard_id, type: Dashboard){
              resource
            }
          }
        """
    )

    params = {"dashboard_id": f"""{dashboard_id}"""}

    # Execute the query on the transport
    try:
        result = client.execute(query, variable_values=params)
        original_stdout = sys.stdout

        # write results to file
        with open(output_file_name, "w", encoding="utf-8") as outfile:
            sys.stdout = outfile  # Change the standard output to the file we created.
            # pylint: disable=unsubscriptable-object;
            print(result["getTerraform"]["resource"])
            sys.stdout = original_stdout  #
    except Exception as e:
        print(str(e))


def get_dashboard_name(dashboard_id):
    """get dashboard terraform from graphql"""
    toke = BEARERTOKEN
    # customer_id = getObserveConfig("customer_id", ENVIRONMENT)
    # Create a GraphQL client using the defined transport
    client = Client(
        transport=RequestsHTTPTransport(
            url=META_URL,
            retries=3,
            headers={"Authorization": f"""Bearer {customer_id} {toke}"""},
        ),
        fetch_schema_from_transport=True,
    )

    # Provide a GraphQL query
    query = gql(
        """
        query dashboard($dashboard_id: ObjectId!){
          dashboard(id:$dashboard_id){
            name
          }
        }
        """
    )

    params = {
        "dashboard_id": f"""{dashboard_id}""",
    }
    # Execute the query on the transport
    result = client.execute(query, variable_values=params)
    # pylint: disable=unsubscriptable-object;
    return result["dashboard"]["name"]


def get_dashboards(workspace_id):
    toke = BEARERTOKEN
    # customer_id = getObserveConfig("customer_id", ENVIRONMENT)
    # Create a GraphQL client using the defined transport
    client = Client(
        transport=RequestsHTTPTransport(
            url=META_URL,
            retries=3,
            headers={"Authorization": f"""Bearer {customer_id} {toke}"""},
        ),
        fetch_schema_from_transport=True,
    )

    # Provide a GraphQL query
    query = gql(
        """
              query dashboards ($workspace_id: [ObjectId!]){
            dashboardSearch(terms: {workspaceId:$workspace_id}) { dashboards {
              dashboard {
                id
                name
                description
                folderId
              }
            }
	
          }
          }
        """
    )

    params = {
        "workspace_id": f"""{workspace_id}""",
    }

    try:
        result = client.execute(query, variable_values=params)
        original_stdout = sys.stdout
        # write results to file
        with open(ALL_DASHBOARDS_JSON_FILE_PATH, "w", encoding="utf-8") as outfile:
            sys.stdout = outfile  # Change the standard output to the file we created.
            # pylint: disable=unsubscriptable-object;
            print(json.dumps(result["dashboardSearch"]["dashboards"], indent=1))
            sys.stdout = original_stdout  #
    except Exception as e:
        print(str(e))

    return ALL_DASHBOARDS_JSON_FILE_PATH


def get_dataset_terraform(dataset_id):
    """get dashboard terraform from graphql"""
    toke = BEARERTOKEN
    # customer_id = getObserveConfig("customer_id", ENVIRONMENT)
    # Create a GraphQL client using the defined transport
    client = Client(
        transport=RequestsHTTPTransport(
            url=META_URL,
            retries=3,
            headers={"Authorization": f"""Bearer {customer_id} {toke}"""},
        ),
        fetch_schema_from_transport=True,
    )

    # Provide a GraphQL query
    query = gql(
        """
          query dataset ($dataset_id: ObjectId!){
            getTerraform(id:$dataset_id, type: Dataset) {
              dataSource
              importName
            }
          }
        """
    )

    params = {
        "dataset_id": f"""{dataset_id}""",
    }

    # Execute the query on the transport
    result = client.execute(query, variable_values=params)

    return result


def get_dashboard_layout(dashboard_id):
    """get dashboard layout from graphql"""
    toke = BEARERTOKEN
    customer_id = getObserveConfig("customer_id", ENVIRONMENT)
    # Create a GraphQL client using the defined transport
    client = Client(
        transport=RequestsHTTPTransport(
            url=META_URL,
            retries=3,
            headers={"Authorization": f"""Bearer {customer_id} {toke}"""},
        ),
        fetch_schema_from_transport=True,
    )

    # Provide a GraphQL query
    query = gql(
        """
          query dash_params($dashboard_id: ObjectId!) {
            dashboard(id:$dashboard_id) {
              layout
            }
          }
        """
    )

    params = {
        "dashboard_id": f"""{dashboard_id}""",
    }

    # Execute the query on the transport
    result = client.execute(query, variable_values=params)

    return result


def get_hidden_params(dashboard_id):
    """get list of isHidden=true params from dash_layout"""
    layout = get_dashboard_layout(dashboard_id)["dashboard"]["layout"]
    dashboard_params = layout["stageListLayout"]["parameters"]
    hidden_params = (
        param for param in dashboard_params if param.get("isHidden", False)
    )

    return hidden_params


def get_param_obj_strings(dashboard_def_string, param_id):
    pattern = '  \{+((?!  \{)[\s\S])*id\s+= "' + param_id + '"((?!  \{)[\s\S])*  \},'
    p = re.compile(pattern)
    return p.finditer(dashboard_def_string)


def write_dashboard(conditional_sections=False):
    """Used to write terraform file"""
    # pylint: disable=invalid-name;
    TMP_FILE_NAME = f"""{OUTPUTFILENAME}_tmp"""

    # writes to temp file
    get_dashboard_terraform(DASHBOARD_ID, TMP_FILE_NAME)

    DASHBOARD_NAME = get_dashboard_name(DASHBOARD_ID)

    # gets list of unique dataset ids to replace
    ids_to_replace = get_ids(TMP_FILE_NAME)

    # # dict for stuff we are replacing
    # stuff_to_replace_dict = {"datasets": []}

    # each dataset id
    for dataset_id in ids_to_replace:
        if len(dataset_id) == 8:
            # get dataset terraform
            result = get_dataset_terraform(dataset_id)

            dataset_obj = {}

            dataset_obj["dataset_id"] = dataset_id
            # pylint: disable=unsubscriptable-object;
            dataset_obj["variable_name"] = result["getTerraform"]["importName"]
            # pylint: disable=unsubscriptable-object;
            dataset_obj["terraform"] = result["getTerraform"]["dataSource"]

            stuff_to_replace_dict["datasets"].append(dataset_obj)

    original_stdout = sys.stdout

    dashboard_local_var_prefix = (
        ## TODO: Add additional escpaing
        f"""{DASHBOARD_NAME.lower()}_dashboard"""
    )
    dashboard_local_var_prefix = re.sub("[\ \(\)\|\\\/]", "_", dashboard_local_var_prefix)
    dashboard_local_var_name = f"""{dashboard_local_var_prefix}_name"""
    # local to write to file
    locals_def = []
    locals_def.append("locals {")
    locals_def.append("workspace = var.workspace.oid")
    locals_def.append(f"""{dashboard_local_var_prefix}_enable = 1""")
    locals_def.append(
        f"""{dashboard_local_var_prefix}_description = \"Add a description here \""""
    )

    locals_def.append(
        f"""{dashboard_local_var_name} = format(var.name_format, "{DASHBOARD_NAME}")"""
    )

    workspace_oid = None

    for line in stuff_to_replace_dict["datasets"]:
        # local variable name
        variable_name = line["variable_name"]
        # add to list to write to file
        locals_def.append(
            f"""{variable_name} = resource.observe_dataset.{variable_name}.id"""
        )
        # get worspace and name for replacement with variables
        workspace_oid = re.findall('workspace[^"]*("[^"]*")', line["terraform"])[0]
        name = re.findall('name[^"]*("[^"]*")', line["terraform"])[0]

        # replace
        line["terraform"] = line["terraform"].replace(
            workspace_oid,
            f"local.workspace \n depends_on = [ resource.observe_dataset.{variable_name}]",
        )
        line["terraform"] = line["terraform"].replace(
            name, f"""format(var.name_format, {name})"""
        )

    if conditional_sections:
        # get original dashboard terraform content
        # this is not consistent with the way we handle replacing strings later on
        # but the strings we want to replace here include newline chars
        # and that wouldn't work with the line-iterative approach we take later.
        with open(TMP_FILE_NAME, "r", encoding="utf-8") as fp:
            dashboard_def_string = fp.read()

        for hidden_param in get_hidden_params(DASHBOARD_ID):
            locals_def.append(
                f"""hidden_param_default_{hidden_param.get("id")} = "replace_me" """
            )
            for match in get_param_obj_strings(
                dashboard_def_string, hidden_param.get("id")
            ):
                # find all the json objects that contain id = param_id
                # and replace their {defaultValue = { string = "" }}
                # with {defaultValue = { string = local.hidden_param_default_param_id }}
                if "defaultValue " in match.group():
                    dashboard_def_string = dashboard_def_string.replace(
                        match.group(),
                        match.group().replace(
                            'string = ""',
                            "string = local.hidden_param_default_{0}".format(
                                hidden_param.get("id")
                            ),
                        ),
                    )

        # overwrite the temp file with hidden param default strings replaced with locals
        with open(TMP_FILE_NAME, "w", encoding="utf-8") as fp:
            fp.write(dashboard_def_string)

    locals_def.append("}")

    # write everything to final terraform file
    with open(OUTPUTFILENAME, "w", encoding="utf-8") as outfile:
        # sys.stdout = outfile  # Change the standard output to the file we created.

        print("#################################")
        print("Locals Definition")
        print("#################################")
        # write local variable definitions
        for local_line in locals_def:
            print(local_line)

        # sys.stdout = original_stdout  #

        print("#################################")
    dashboard_lines = []

    # read dashboard temp file into lines
    with open(TMP_FILE_NAME, "r", encoding="utf-8") as fp:
        # read an store all lines into list
        dashboard_lines = fp.readlines()

    # replace dataset ids with variable and write to file
    with open(OUTPUTFILENAME, "a", encoding="utf-8") as fp:
        for i, line in enumerate(dashboard_lines):
            if i == 2:
                new_line = f"""count = local.{dashboard_local_var_prefix}_enable\n"""
                fp.write(new_line)

                new_line2 = f"""description = local.{dashboard_local_var_prefix}_description\n"""
                fp.write(new_line2)

            for dataset_line in stuff_to_replace_dict["datasets"]:
                # pylint: disable=line-too-long;
                line = line.replace(
                    '"{0}"'.format(dataset_line["dataset_id"]),
                    "local.{0}".format(dataset_line["variable_name"]),
                )

            if workspace_oid in line:
                line = line.replace(workspace_oid, "local.workspace")

            if DASHBOARD_NAME in line:
                line = line.replace(
                    DASHBOARD_NAME, f"""local.{dashboard_local_var_name}"""
                )
                line = re.sub(r"\"", "", line)

            fp.write(line)

    os.remove(TMP_FILE_NAME)

    terraform_command = f"terraform fmt {OUTPUTFILENAME}"
    os.system(terraform_command)


parser = argparse.ArgumentParser(description="Observe UI to Terraform Object script")
parser.add_argument(
    "-d",
    dest="dash_id",
    action="store",
    help="integer ID for dashboard",
    default=123456,
)
parser.add_argument(
    "-e",
    dest="env",
    action="store",
    help="name of environment set in config.ini file in brackets",
)
parser.add_argument(
    "-w",
    dest="workspace_id",
    action="store",
    help="ID of workspace - required when running fetch worksheets",
)
parser.add_argument(
    "-n",
    dest="output_name",
    action="store",
    help="(Optional) file name to output to. Default is output.tf",
)
# parser.add_argument(
#     "-t",
#     dest="bearer_token",
#     action="store",
#     help="(Optional) Bearer token for authorization. Useful for SSO accounts",
# )
parser.add_argument(
    "-v",
    dest="is_debug",
    default=False,
    action="store_true",
    help="(Optional) Enable debug logging",
)
parser.add_argument(
    "-c",
    dest="config_path",
    # default="config.ini",
    action="store",
    help="(Optional) Set path to config.ini. E.g, /Users/Hagrid/github.com/content-eng-tools/auto-magical-dashboard/config.ini",
)

parser.add_argument(
    "--customer",
    default=os.environ.get("OBSERVE_CUSTOMER"),
    help="Observe customer ID",
)
parser.add_argument(
    "--domain",
    default=os.environ.get("OBSERVE_DOMAIN", "observeinc.com"),
    help="Observe domain",
)
parser.add_argument(
    "--user-email",
    default=os.environ.get("OBSERVE_USER_EMAIL"),
    help="Observe user email",
)

auth = parser.add_mutually_exclusive_group()
auth.add_argument(
    "--user-password",
    default=os.environ.get("OBSERVE_USER_PASSWORD"),
    help="Observe user email",
)
auth.add_argument(
    "-t",
    dest="bearer_token",
    action="store",
    help="(Optional) Bearer token for authorization. Useful for SSO accounts",
)

parser.add_argument(
    "--conditional_sections",
    dest="conditional_sections",
    default=False,
    action="store_true",
    help="(Experimental) Enable Conditional Section Edits and Locals",
)

parser.add_argument(
    "--fetch_dashboards",
    dest="fetch_dashboards",
    default="False",
    action="store_true",
    help="Create list of dashboards",
)

parser.add_argument(
    "--fetch_datasets",
    dest="fetch_datasets",
    default="False",
    action="store_true",
    help="Create unique list of datasets from dashboards",
)

parser.add_argument(
    "--make_locals",
    dest="make_locals",
    default="False",
    action="store_true",
    help="Makes local file",
)
parser.add_argument(
    "--export_dashboards",
    dest="export_dashboards",
    default="False",
    action="store_true",
    help="Export list of dashboards",
)


args = parser.parse_args()

if args.is_debug:
    logging.basicConfig(level=logging.DEBUG)

ENVIRONMENT = args.env
# if args.config_path == "NoneType":
if args.config_path is not None:
    print("Using Config File for Login")
    customer_id = getObserveConfig("customer_id", ENVIRONMENT)
    domain = getObserveConfig("domain", ENVIRONMENT)
    user_email = getObserveConfig("user_email", ENVIRONMENT)
    user_password = getObserveConfig("user_password", ENVIRONMENT)
else:
    print("Using Environment Variables for Login")
    customer_id = args.customer
    domain = args.domain
    user_email = args.user_email
    user_password = args.user_password

OUTPUTFILENAME = args.output_name if args.output_name else "output.tf"
BEARERTOKEN = args.bearer_token if args.bearer_token else get_bearer_token()

DASHBOARD_ID = args.dash_id

# customer_id = getObserveConfig("customer_id", ENVIRONMENT)
# domain = getObserveConfig("domain", ENVIRONMENT)
META_URL = f"https://{customer_id}.{domain}/v1/meta"

print("dashboard id:", DASHBOARD_ID)
print("file name:", OUTPUTFILENAME)

OUTPUT_EXISTS = os.path.exists(OUTPUTFILENAME)

ROOT_OUTPUT_DIR = "terraform_generated"
JSON_DIR = "json_files"

ALL_DASHBOARDS_JSON_FILE_PATH = f"""{ROOT_OUTPUT_DIR}/{JSON_DIR}/all_dashboards.json"""
DATASET_FILE_PATH = f"""{ROOT_OUTPUT_DIR}/{JSON_DIR}/all_datasets.json"""
DATASET_FILE_PATH_ORIG = f"""{ROOT_OUTPUT_DIR}/{JSON_DIR}/all_datasets_orig.json"""
LOCALS_FILE_PATH = f"""{ROOT_OUTPUT_DIR}/locals.tf"""
OUTPUTFILENAME_FMT = "{ROOT_OUTPUT_DIR}/i_{DASHBOARD_ID}.tf"
TMP_FILE_NAME_FMT = "{ROOT_OUTPUT_DIR}/tmp/i_{DASHBOARD_ID}.tmp"

pathlib.Path(f"""{ROOT_OUTPUT_DIR}/{JSON_DIR}""").mkdir(parents=True, exist_ok=True)
pathlib.Path(f"""{ROOT_OUTPUT_DIR}/tmp""").mkdir(parents=True, exist_ok=True)

#dashIDs = ["41015790","41011423","41002596","41002614","41002603","41013316","41013535","41013796","41013545","41014136","41014718","41013284","41014705","41014817","41015706","41015806","41013247","41013711","41013378","41015626","41013300","41013454","41013660","41013454","41012210","41013486","41014520","41014632","41015762","41013677","41013768","41014556","41013805","41013407","41013534","41011620","41012338","41003397","41014456","41016017","41016020","41016557","41016472","41016568","41016561","41016565","41016088","41016475","41016474","41016652","41017002","41016018","41014473","41016025"]
#dashIDs = ["41016834","41016314"]

# dict for stuff we are replacing
stuff_to_replace_dict = {"datasets": []}

if args.conditional_sections:
    write_dashboard(conditional_sections=True)

# Fetch Dashboards
if args.workspace_id == None:
    raise ValueError("Need to provide a workspace id using -w flag.")
get_dashboards(args.workspace_id)

# Fetch datasets
with open(ALL_DASHBOARDS_JSON_FILE_PATH, "r", encoding="utf-8") as outfile:
    dashboards = json.load(outfile)
    for board in dashboards:
        if board["dashboard"]["id"] == DASHBOARD_ID:
            print(board["dashboard"]["id"])
            DASHBOARD_ID = board["dashboard"]["id"]
            OUTPUTFILENAME = OUTPUTFILENAME_FMT.format(
                ROOT_OUTPUT_DIR=ROOT_OUTPUT_DIR, DASHBOARD_ID=DASHBOARD_ID
            )
            TMP_FILE_NAME = TMP_FILE_NAME_FMT.format(
                ROOT_OUTPUT_DIR=ROOT_OUTPUT_DIR, DASHBOARD_ID=DASHBOARD_ID
            )

            # writes to temp file
            get_dashboard_terraform(DASHBOARD_ID, TMP_FILE_NAME)

            DASHBOARD_NAME = get_dashboard_name(DASHBOARD_ID)

            # gets list of unique dataset ids to replace
            ids_to_replace = get_ids(TMP_FILE_NAME)

            print("\n================================")
            print(DASHBOARD_NAME, " - ", DASHBOARD_ID)
            print("ids to replace - ", ids_to_replace)
            print("\n================================")
            # each dataset id
            for dataset_id in ids_to_replace:
                print("Fetching dataset - ", dataset_id)
                if len(dataset_id) == 8:
                    # get dataset terraform
                    try:
                        result = get_dataset_terraform(dataset_id)
                        dataset_obj = {}

                        dataset_obj["dataset_id"] = dataset_id
                        # pylint: disable=unsubscriptable-object;
                        dataset_obj["variable_name"] = result["getTerraform"][
                            "importName"
                        ]
                        variable_name = dataset_obj["variable_name"]
                        # pylint: disable=unsubscriptable-object;
                        dataset_obj["terraform"] = result["getTerraform"]["dataSource"]

                        # get worspace and name for replacement with variables
                        workspace_oid = re.findall(
                            'workspace[^"]*("[^"]*")', dataset_obj["terraform"]
                        )[0]
                        name = re.findall(
                            'name[^"]*("[^"]*")', dataset_obj["terraform"]
                        )[0]

                        # replace
                        dataset_obj["terraform"] = dataset_obj["terraform"].replace(
                            workspace_oid,
                            f"local.workspace \n depends_on = [ resource.observe_dataset.{variable_name}]",
                        )
                        dataset_obj["terraform"] = dataset_obj["terraform"].replace(
                            name, f"""format(var.name_format, {name})"""
                        )

                        stuff_to_replace_dict["datasets"].append(dataset_obj)
                    except Exception as e:
                        print(str(e))
                        print("input fetch flamed - you probably have a bad input")
                        pass

# write results to file
with open(DATASET_FILE_PATH, "w", encoding="utf-8") as outfile:
    deduplicate_dict = {}

    original_stdout = sys.stdout

    with open(f"""{DATASET_FILE_PATH_ORIG}""", "w", encoding="utf-8") as outfile2:
        sys.stdout = outfile2
        print(json.dumps(stuff_to_replace_dict, indent=1))

    # sys.stdout = original_stdout

    for index, element in enumerate(stuff_to_replace_dict["datasets"]):
        deduplicate_dict[element["dataset_id"]] = {}
        deduplicate_dict[element["dataset_id"]]["variables"] = element[
            "variable_name"
        ]
        deduplicate_dict[element["dataset_id"]]["terraform"] = element["terraform"]

    sys.stdout = outfile  # Change the standard output to the file we created.

    # pylint: disable=unsubscriptable-object;
    print(json.dumps(deduplicate_dict, indent=1))
    sys.stdout = original_stdout  #

# Make Locals
with open(ALL_DASHBOARDS_JSON_FILE_PATH, "r", encoding="utf-8") as outfile:
    dashboards = json.load(outfile)
    # local to write to file
    locals_def = []
    locals_def.append("locals {")
    locals_def.append("workspace = var.workspace.oid")
    locals_def.append("name_format = var.name_format")

    for board in dashboards:
        if board["dashboard"]["id"] == DASHBOARD_ID:
            print(board["dashboard"]["id"])
            DASHBOARD_ID = board["dashboard"]["id"]
            DASHBOARD_NAME = board["dashboard"]["name"]

            dashboard_local_var_prefix = (
                f"""{DASHBOARD_NAME.lower()}_dashboard"""
            )

            dashboard_local_var_prefix = re.sub("[\ \(\)\|\\\/]", "_", dashboard_local_var_prefix)

            dashboard_local_var_name = f"""{dashboard_local_var_prefix}_name"""

            locals_def.append(f"""{dashboard_local_var_prefix}_enable = 1""")
            locals_def.append(
                f"""{dashboard_local_var_prefix}_description = \"Add a description here \""""
            )

            locals_def.append(
                f"""{dashboard_local_var_name} = format(local.name_format, "{DASHBOARD_NAME}")"""
            )

workspace_oid = None

with open(DATASET_FILE_PATH, "r", encoding="utf-8") as datasets_file:
    datasets = json.load(datasets_file)
    for key in datasets.keys():
        # local variable name
        print("################################")
        print("key: ", key)
        print("################################")
        variable_name = datasets[key]["variables"]
        # add to list to write to file
        locals_def.append(
            f"""{variable_name} = resource.observe_dataset.{variable_name}.id"""
        )
        # get worspace and name for replacement with variables
        workspace_oid = re.findall(
            'workspace[^"]*("[^"]*")', datasets[key]["terraform"]
        )[0]
        name = re.findall('name[^"]*("[^"]*")', datasets[key]["terraform"])[0]

        # replace
        datasets[key]["terraform"] = datasets[key]["terraform"].replace(
            workspace_oid,
            f"local.workspace \n depends_on = [ resource.observe_dataset.{variable_name}]",
        )
        datasets[key]["terraform"] = datasets[key]["terraform"].replace(
            name, f"""format(var.name_format, {name})"""
        )

    # if args.conditional_sections:
    #     # get original dashboard terraform content
    #     # this is not consistent with the way we handle replacing strings later on
    #     # but the strings we want to replace here include newline chars
    #     # and that wouldn't work with the line-iterative approach we take later.
    #     with open(TMP_FILE_NAME, "r", encoding="utf-8") as fp:
    #         dashboard_def_string = fp.read()

    #     for hidden_param in get_hidden_params(DASHBOARD_ID):
    #         locals_def.append(
    #             f"""hidden_param_default_{hidden_param.get("id")} = "replace_me" """
    #         )
    #         for match in get_param_obj_strings(
    #             dashboard_def_string, hidden_param.get("id")
    #         ):
    #             # find all the json objects that contain id = param_id
    #             # and replace their {defaultValue = { string = "" }}
    #             # with {defaultValue = { string = local.hidden_param_default_param_id }}
    #             if "defaultValue " in match.group():
    #                 dashboard_def_string = dashboard_def_string.replace(
    #                     match.group(),
    #                     match.group().replace(
    #                         'string = ""',
    #                         "string = local.hidden_param_default_{0}".format(
    #                             hidden_param.get("id")
    #                         ),
    #                     ),
    #                 )

    #     # overwrite the temp file with hidden param default strings replaced with locals
    #     with open(TMP_FILE_NAME, "w", encoding="utf-8") as fp:
    #         fp.write(dashboard_def_string)

    locals_def.append("}")

    with open(LOCALS_FILE_PATH, "w", encoding="utf-8") as locals_file:
        for line in locals_def:
            locals_file.write(f"""{line} \n""")

    terraform_command = f"terraform fmt {LOCALS_FILE_PATH}"
    os.system(terraform_command)

# Export dashboards
workspace_oid = None

with open(ALL_DASHBOARDS_JSON_FILE_PATH, "r", encoding="utf-8") as outfile:
    dashboards = json.load(outfile)
    for board in dashboards:
        if board["dashboard"]["id"] == DASHBOARD_ID:
            print(board["dashboard"]["id"])
            DASHBOARD_ID = board["dashboard"]["id"]
            OUTPUTFILENAME = OUTPUTFILENAME_FMT.format(
                ROOT_OUTPUT_DIR=ROOT_OUTPUT_DIR, DASHBOARD_ID=DASHBOARD_ID
            )
            TMP_FILE_NAME = TMP_FILE_NAME_FMT.format(
                ROOT_OUTPUT_DIR=ROOT_OUTPUT_DIR, DASHBOARD_ID=DASHBOARD_ID
            )

            # writes to temp file
            get_dashboard_terraform(DASHBOARD_ID, TMP_FILE_NAME)

            DASHBOARD_NAME = get_dashboard_name(DASHBOARD_ID)

            # gets list of unique dataset ids to replace
            ids_to_replace = get_ids(TMP_FILE_NAME)

            print("\n================================")
            print(DASHBOARD_NAME, " - ", DASHBOARD_ID)
            print("ids to replace - ", ids_to_replace)
            print("\n================================")
            # each dataset id
            for dataset_id in ids_to_replace:
                print("Fetching dataset - ", dataset_id)
                if len(dataset_id) == 8:
                    # get dataset terraform
                    try:
                        result = get_dataset_terraform(dataset_id)
                        dataset_obj = {}

                        dataset_obj["dataset_id"] = dataset_id
                        # pylint: disable=unsubscriptable-object;
                        dataset_obj["variable_name"] = result["getTerraform"][
                            "importName"
                        ]
                        variable_name = dataset_obj["variable_name"]
                        # pylint: disable=unsubscriptable-object;
                        dataset_obj["terraform"] = result["getTerraform"]["dataSource"]

                        # get worspace and name for replacement with variables
                        workspace_oid = re.findall(
                            'workspace[^"]*("[^"]*")', dataset_obj["terraform"]
                        )[0]
                        name = re.findall(
                            'name[^"]*("[^"]*")', dataset_obj["terraform"]
                        )[0]

                        # replace
                        dataset_obj["terraform"] = dataset_obj["terraform"].replace(
                            workspace_oid,
                            f"local.workspace \n depends_on = [ resource.observe_dataset.{variable_name}]",
                        )
                        dataset_obj["terraform"] = dataset_obj["terraform"].replace(
                            name, f"""format(var.name_format, {name})"""
                        )

                        stuff_to_replace_dict["datasets"].append(dataset_obj)
                    except Exception as e:
                        print(str(e))
                        print("input fetch flamed - you probably have a bad input")
                        pass

with open(ALL_DASHBOARDS_JSON_FILE_PATH, "r", encoding="utf-8") as outfile:
    dashboards = json.load(outfile)
    print(stuff_to_replace_dict)
    for board in dashboards:
        if board["dashboard"]["id"] == DASHBOARD_ID:
            print(board["dashboard"]["id"])
            DASHBOARD_ID = board["dashboard"]["id"]
            DASHBOARD_NAME = board["dashboard"]["name"]
            OUTPUTFILENAME = OUTPUTFILENAME_FMT.format(
                ROOT_OUTPUT_DIR=ROOT_OUTPUT_DIR, DASHBOARD_ID=DASHBOARD_ID
            )
            TMP_FILE_NAME = TMP_FILE_NAME_FMT.format(
                ROOT_OUTPUT_DIR=ROOT_OUTPUT_DIR, DASHBOARD_ID=DASHBOARD_ID
            )

            dashboard_local_var_prefix = (
                f"""{DASHBOARD_NAME.lower()}_dashboard"""
            )

            dashboard_local_var_prefix = re.sub("[\ \(\)\|\/]", "_", dashboard_local_var_prefix)

            dashboard_local_var_name = f"""{dashboard_local_var_prefix}_name"""
            # write everything to final terraform file
            dashboard_lines = []

            # read dashboard temp file into lines
            with open(TMP_FILE_NAME, "r", encoding="utf-8") as fp:
                # read an store all lines into list
                dashboard_lines = fp.readlines()

            # replace dataset ids with variable and write to file
            with open(OUTPUTFILENAME, "a", encoding="utf-8") as fp:
                for i, line in enumerate(dashboard_lines):
                    if i == 2:
                        new_line = (
                            f"""count = local.{dashboard_local_var_prefix}_enable\n"""
                        )
                        fp.write(new_line)

                        new_line2 = f"""description = local.{dashboard_local_var_prefix}_description\n"""
                        fp.write(new_line2)

                    for dataset_line in stuff_to_replace_dict["datasets"]:
                        # pylint: disable=line-too-long;
                        line = line.replace(
                            '"{0}"'.format(dataset_line["dataset_id"]),
                            "local.{0}".format(dataset_line["variable_name"]),
                        )
                    workspace_oid = re.findall('workspace[^"]*("[^"]*")', line)

                    if len(workspace_oid) > 0:
                        line = line.replace(workspace_oid[0], "local.workspace")

                    if DASHBOARD_NAME in line:
                        line = line.replace(
                            DASHBOARD_NAME, f"""local.{dashboard_local_var_name}"""
                        )
                        line = re.sub(r"\"", "", line)

                    fp.write(line)

            # os.remove(TMP_FILE_NAME)

            terraform_command = f"terraform fmt {OUTPUTFILENAME}"
            os.system(terraform_command)


#else:
#    write_dashboard()

# pylint: disable=pointless-string-statement;
"""
query terraform {
      getTerraform( id:"41143378", type: Dashboard){
        resource
      }
    }

    python3 writeTerraform.py db.json

    grep -rh "datasetId" --include \*.tf | sed -e $'s/,/\\\n/g' | sed -e 's/[[:space:]]//g' | sort | uniq | sed -e 's/"datasetId"://g'

    query datasets {
      datasetSearch(labelMatches:["GCP/Compute"]){
        dataset {
          id
          name
          kind
          label
          workspaceId
        }
      }
    }

     sed -i '' "s:41143354:"\${local.COMPUTE_INSTANCE}":g" *.tf
"""
