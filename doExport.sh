#!/bin/bash
./write_terraform.py -c ../../config.ini -e stagingdemo -w 41006584 -d 43689653 --fetch_dashboards
./write_terraform.py -c ../../config.ini -e stagingdemo -w 41006584 -d 43689653 --fetch_datasets
./write_terraform.py -c ../../config.ini -e stagingdemo -d 43689653 --make_locals
./write_terraform.py -c ../../config.ini -e stagingdemo -d 43689653 --export_dashboards
