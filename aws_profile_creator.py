__author__ = 'Mark Mon Monteros'

from pathlib import Path
import os, sys, random, subprocess
import boto3
import pandas as pd
import pyperclip

class AWSProfileGenerator():

    def __init__(self):
        self.org = boto3.client('organizations')
        self.homedir = Path.home()
        self.accts = []
        self.newacct = []
        self.region = []
        self.proj_dir = Path(os.path.dirname(os.path.realpath(__file__)))
        self.proj_aws_cfg = self.proj_dir.joinpath('config')
        self.proj_ext_cfg = self.proj_dir.joinpath('config-chrome-ext')
        self.aws_cfg = self.homedir.joinpath('.aws').joinpath('config')
        self.ext_cfg = self.homedir.joinpath('.aws').joinpath('config')

        print('proj_aws_cfg: ', self.proj_aws_cfg)
        print('proj_ext_cfg: ', self.proj_ext_cfg)
        print('aws_cfg: ', self.aws_cfg)

        print('\nChecking AWS Config files...')

        if not os.path.exists(self.aws_cfg):
            print('\nNo ' + str(os.path.split(self.aws_cfg)[1]) + ' found. Creating...' + str(self.aws_cfg))
            os.remove(self.aws_cfg)
            # open(self.aws_cfg, "w").close()

        self.acct = self.pull_accounts()
        self.get_region()
        self.add_aws_profile()
        self.add_ext_profile()

    def pull_accounts(self):
        print('\nChoose Organization Unit:')
        print('\t[1] - Prod')
        print('\t[2] - Sandbox')
        print('\t[3] - AWS 2.0 Customers')
        print('\t[4] - Security')
        print('\t[5] - AFT Management')
        print('\t[6] - Infrastructure Prod')
        print('\t[Any other keys] - default to (Prod)')
        num = input('\nEnter number: ')
        match num:
            case "1":
                org = 'ou-mpfo-uv6625zp'
                print('\nPROD selected.')
            case "2":
                org = 'ou-mpfo-oi46con6'
                print('\nSandbox selected.')
            case "3":
                org = 'ou-mpfo-zyinzmm1'
                print('\nAWS 2.0 Customers selected.')
            case "4":
                org = 'ou-mpfo-ohcjkjws'
                print('\nSecurity selected.')
            case "5":
                org = 'ou-mpfo-ostkhvjm'
                print('\nAFT Management selected.')
            case "6":
                org = 'ou-mpfo-0abuufkh'
                print('\nInfrastructure Prod selected.')
            case _:
                org = 'ou-mpfo-uv6625zp'
                print('\nPROD OU selected.')

        print('\nPulling Latest Account List from ' + org + '...')

        paginator = self.org.get_paginator('list_accounts_for_parent')
        page_iterator = paginator.paginate(ParentId=org)
        for page in page_iterator:
            for acct in page['Accounts']:
                self.accts.append(acct)

        for i in self.accts:
            ps = subprocess.Popen(['grep', '-irnw', self.aws_cfg, '-e', i['Id']], 
                            stdout=subprocess.PIPE)
            output = ps.stdout.readline()
            return_code = ps.poll()
            
            if return_code == 1:
                self.newacct.append(i)

        if not self.newacct:
            print('\nNo New Accounts. Exiting...')
            self.exit()

        else:
            print('\nNew Account/s Detected :')
            for i in self.newacct:
                print(u"\n\t\u2713 " + i['Name'] + ' | ' + i['Id'] + ' | ' + i['Email'])

            return self.newacct

    def get_region(self):
        # Download this worksheet --> https://sapphire365.sharepoint.com/sites/SapphireBeyondProgramme/_layouts/15/Doc.aspx?sourcedoc=%7B1417A7B3-CD5E-4ABF-A484-10F5E496496F%7D&file=Sapphire%20BeyondProgramme_Closure.pptx&action=edit&mobileredirect=true&CT=1671183012457&OR=ItemsView
        # Commented codes here are xlsx to csv conversion
        xls_file = self.homedir.joinpath('Downloads').joinpath('Sapphire Migration Inventory.xlsx')
        csv_file = self.homedir.joinpath('Downloads').joinpath('Sapphire Migration Inventory.csv')
        checkXLS = os.path.exists(xls_file)

        try:
            with open (csv_file, 'r', encoding='UTF-8') as accts_csv:
                df = pd.read_csv(accts_csv)
                df2 = df[['Name', 'AWS MBN Prod Account ', 'Region']]
        except:
            if not checkXLS:
                print('\nPlease download the Sapphire Migration Inventory file: \n\thttps://sapphire365.sharepoint.com/:x:/s/SapphireBeyondProgramme/EUXa8Rf4iR5Gjf5SeHba_XcBebR7rsVhMxinEDt2vRCOMA?e=Umcp52')
                self.exit()
            else:
                print('\nConverting ' + str(xls_file) + ' to CSV...')
                df = pd.read_excel(xls_file, 'Customer Contacts and Plan', index_col=None)
                # warnings.simplefilter(action='ignore', category=UserWarning)
                df.to_csv(os.path.splitext(xls_file)[0] + '.csv')
                print('\nDone: ' + str(csv_file))

        with open (csv_file, 'r', encoding='UTF-8') as accts_csv:
            df = pd.read_csv(accts_csv)
            df2 = df[['Name', 'AWS MBN Prod Account ', 'Region']]

        for i in self.acct:
            for data in df2.values:
                if i['Email'] == data[1]:
                    if data[2] == 'UK':
                        i['Region'] = 'eu-west-2'
                        self.region.append(i)
                    elif data[2] == 'US':
                        i['Region'] = 'us-east-2'
                        self.region.append(i)
                    else:
                        print('\nNo Region Data found in CSV File. \n\nPlease specify region for >>> ' + i['Name'])
                        i['Region'] = self.input_region()
                        self.region.append(i)
                        print(u"\n\t\u2713 Region: " + i['Region'])
                    break

        noreg = [i for i in self.acct if i not in self.region]

        for i in noreg:
            print('\nNo Region Data found in CSV File. \n\nPlease specify region for >>> ' + i['Name'])
            i['Region'] = self.input_region()
            self.region.append(i)
            print(u"\n\t\u2713 Region: " + i['Region'])

    def input_region(self):
        print('\nChoose Region:')
        print('\t[1] - eu-west-2 (London)')
        print('\t[2] - us-east-2 (Ohio)')
        print('\t[0] - Specify region name')
        print('\t[Any other keys] - default to eu-west-2 (London)')
        num = input('\nEnter number: ')
        match num:
            case "0":
                region = input('\nEnter region name: ')
                return region
            case "1":
                region = 'eu-west-2'
                return region
            case "2":
                region = 'us-east-2'
                return region
            case _:
                region = 'eu-west-2'
                return region

    def add_aws_profile(self):
        for i in self.region:
            with open (self.aws_cfg, 'a') as aws_config:
                aws_config.write('\n[{profilename}]'.format(profilename=i['Name']).lower().replace('_','-'))
                aws_config.write('\nrole_arn = arn:aws:iam::{accountId}:role/OrganizationAccountAccessRole'.format(accountId=i['Id']))
                aws_config.write('\nregion = {region}'.format(region=i['Region']))
                aws_config.write('\nsource_profile = sapphire-payer\n')

        print('\nNew Profile added to ' + str(self.aws_cfg) + '\n')

    def add_ext_profile(self):
        for i in self.region:
            with open (self.ext_cfg, 'a') as ext_config:
                ext_config.write('\n[{profilename}]'.format(profilename=i['Name']).lower().replace('_','-'))
                ext_config.write('\nrole_arn = arn:aws:iam::{accountId}:role/OrganizationAccountAccessRole'.format(accountId=i['Id']))
                ext_config.write('\nregion = {region}'.format(region=i['Region']))
                ext_config.write('\ncolor = {color}\n'.format(color=self.gen_hexcolor()))

        print('\nNew Profile added to ' + str(self.ext_cfg) + '\n')

        ps = subprocess.run(['cat', self.ext_cfg], 
                                    check=True, 
                                    capture_output=True)
        psNames = subprocess.run(['tail', '-n', str(len(self.region) * 5)],
                                    input=ps.stdout,
                                    capture_output=True)
        output = psNames.stdout.decode('utf-8').strip()

        pyperclip.copy(output)

        print('\nNOTE: Paste clipboard now to AWS Extend Switch Roles Chrome Extension...\n')

    def gen_hexcolor(self):
        r = lambda: random.randint(0,255)
        return str('%02X%02X%02X' % (r(),r(),r())).lower()

    def exit(self):
        sys.exit(0)


if __name__ == '__main__':
    print('\n>> AWS Profile Creator <<')
    print('\nCreated by: ' + __author__)
    
    print("\nNOTE: awsume to sapphire-payer profile before running script.\n")
    
    AWSProfileGenerator()
    
    print('\n\nDONE...!!!\n')
