# Observe Dashboard Terraform

This script is to ease the process of exporting an existing dashboard from Observe and placing that into an exiting terraform repository.

## Requirements

- Python 3
- The following Python modules
  - `requests`
  - `requests_toolbelt`
  - `gql`

## Usage

First configure the `config.ini` file with a block for the source tenant for the dashboard

```
[example]
customer_id = 12345678910
user_email = example@user.com
user_password = thisISaPASSWORD
domain = observeinc.com
```

`customer_id` is the string of digits at the start of your Observe URL, `domain` is from the rest of the domain. For example for the following Observe URL `https://1111333444.eu-1.observeinc.com` then `customer_id` is `1111333444` and `domain` is `eu-1.observeinc.com`. Username and password are you access credentials.

To perform en export, an example is the following

`./write_terraform.py -c ./config.ini -e example -w 41006584 -d 41570960`

Where:
- '-c' is the path to `config.ini`
- `-e` is the environment block in the `config.ini` file 
- `-w` is the workspace id, this appears in the dashboard URL right after `/workspace/`
- `-d` is the dashboard id, this appears at the end of the dashboard URL

This is the dashboard URL for the above example `https://12345678910.observeinc.com/workspace/41006584/dashboard/System-Overview-41570960`

This will produce a directory called `terraform_generated`, this contains 3 items to move into the target Terraform modules
- `i_41570960.tf`, where the ID matches that of the dashboard, this is the TF definition
- `json_files`, this contains the JSON defintion of the dashboard, this is referened from the above `tf` file
- `locals.tf`, this contains the variables that will be populated into the defintion