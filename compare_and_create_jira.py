
from bs4 import BeautifulSoup
import urllib.request as urllib2
import csv
import pandas as pd
import sys
import numpy as np
from helper import JiraHelper


print ("Environment1 to be compared: ",sys.argv[1])
print ("Environment2 to be compared: ",sys.argv[2])

ENV1 = sys.argv[1]
ENV2 = sys.argv[2]
OWNER = sys.argv[3]
RELEASE = sys.argv[4]
CREATE_JIRA_FLAG_ENABLED = sys.argv[5]


def create_jira(service_name, source, sha_on_env1, sha_on_env2, release, release_coordinator):
    try:
        user_name = ""
        api_token = ""
        server = ""
        jira = JiraHelper(user_name, api_token, server)

        # Test Data for Creating Issue
        test_data = {
            "project": "QA",
            "summary": "Sample summary for " +ENV1 + " VS "+ ENV2  ,
            "description": "Sample description for  : "+ ENV1 +" and "+ ENV2+" \n",
            "issuetype": {"name": "Task"}
        }
        print("Payload for creation of Jira: " + str(test_data))

        # Creating Test in Jira
        issues = jira.create_issue(test_data)
        print("Jira created is " + issues.key)
        isJiraAssigned = jira.assign_issue( issues.key, release_coordinator)
        print("Jira Assigned? " + isJiraAssigned)
        jira.update_issue_fields(issues.key, {'fixVersions': [{'name': release}]})
    except:
        print("An exception occurred while creating or updating the jira" )



#call the deploy environment and get the hashes
def get_hashes_from_deploy_environment(environment):
    url = '' + environment
    print(url)
    html = urllib2.urlopen(url).read()
    soup = BeautifulSoup(html,features="lxml")
    table = soup.select_one("table.service-table")
    # python3 just use th.text
    headers = [th.text for th in table.select("tr th")]

    with open("environment.csv", "w") as f:
        wr = csv.writer(f)
        wr.writerow(headers)
        wr.writerows([[td.text for td in row.find_all("td")] for row in table.select("tr + tr")])

    my_filtered_csv = pd.read_csv("environment.csv", usecols=['Service', 'Sha', 'Source'])
    return my_filtered_csv

ENV1_HAHES_DF1 =get_hashes_from_deploy_environment(ENV1)
ENV2_HAHES_DF2=get_hashes_from_deploy_environment(ENV2)
df_all_services = pd.concat([ENV1_HAHES_DF1.set_index('Service'), ENV2_HAHES_DF2.set_index('Service')],
                 axis='columns', keys=[ENV1, ENV2])
df_final = df_all_services.swaplevel(axis='columns')[ENV1_HAHES_DF1.columns[1:]]#


def highlight_diff(data, color='yellow'):
    attr = 'background-color: {}'.format(color)
    other = data.xs(ENV1, axis='columns', level=-1)
    return pd.DataFrame(np.where(data.ne(other, level=0), attr, ''),
                        index=data.index, columns=data.columns)

def log_jira():
    #Gather data
    ENV1_HAHES_DF1 =get_hashes_from_deploy_environment(ENV1)
    ENV2_HAHES_DF2=get_hashes_from_deploy_environment(ENV2)
    ENV1_HAHES_DF1=ENV1_HAHES_DF1.rename(columns={'Deployed Branch-Sha': 'Sha-'+ENV1})
    ENV1_HAHES_DF1=ENV1_HAHES_DF1.rename(columns={'Source': 'Source-'+ENV1})
    ENV2_HAHES_DF2=ENV2_HAHES_DF2.rename(columns={'Deployed Branch-Sha': 'Sha-'+ENV2})
    ENV2_HAHES_DF2=ENV2_HAHES_DF2.rename(columns={'Source': 'Source-'+ENV2})
    #Merge the data
    df_concat_services = pd.merge(ENV1_HAHES_DF1, ENV2_HAHES_DF2, on='Service', how='outer')
    df_concat_services.fillna('')
    df_concat_services = df_concat_services.reset_index()  # make sure indexes pair with number of rows
    #iterate over the services
    with open("config/exclusion.txt", 'r', encoding='UTF-8') as file:
        lines = [line.rstrip() for line in file]
    print("The config file exclusion has below content:" + str(lines))
    for index, row in df_concat_services.iterrows():
        if(row['Deployed-Branch-Sha-'+ENV1]!=row['Sha-'+ENV2]):
            if any(exclusion in row['Service'] for exclusion in lines):
                print(row['Service'] + " will be excluded from creating jira")
                exit
            else:
                print("creating/updating jira for: " + row['Service'])
                #Create-updateJira
                create_jira(row['Service'], row['Source-'+ENV1], row['Sha-'+ENV1], row['Sha-'+ENV2], RELEASE, OWNER)


html_result=df_final.style.apply(highlight_diff, axis=None).render()
text_file = open("Report/index.html", "w")
text_file.write(html_result)
text_file.close()
if CREATE_JIRA_FLAG_ENABLED == "true":
    log_jira()
