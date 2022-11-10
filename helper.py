import jira.client


class JiraHelper:

    def __init__(self, user_name, api_token, server):
        self.jira = jira.client.JIRA(basic_auth=(user_name, api_token), options={"server": server})

    def create_issue(self, test_data):
        try:
            issue_key = self.jira.create_issue(fields=test_data)
            return issue_key
        except:
            print("An exception occurred while creating the jira")

    def update_issue_fields(self, issue_key, updated_test_data):
        try:
            issue = self.jira.issue(issue_key)
            issue.update(fields=updated_test_data)
        except:
            print("An exception occurred while updating the jira")

    def delete_issue(self, issue_key):
        try:
            issue = self.jira.issue(issue_key)
            issue.delete()
        except:
            print("An exception occurred while deleting the jira")

    def search_issue(self, test_data):
        try:
            issue_key = self.jira.search_issues(fields=test_data)
            return issue_key
        except:
            print("An exception occurred while searching the jira")

    def assign_issue(self, issue_key, test_data):
        try:
            isUssueAssigned = self.jira.assign_issue(issue_key, test_data)
            return isUssueAssigned
        except:
            print("An exception occurred while searching the jira")

    def get_user_identifier(self, test_data):
        accountID = self.jira._get_user_identifier(fields=test_data)
        return accountID

    def create_version_if_not_exist(self, project, release_name):
        """Check if version exist"""
        # New version is in the last element of the list
        version = self.jira.project_versions(project)[-1]

        if str(version) == release_name:
            print ("Release version exists")
        else:
            #return False
            self.create_version(project, release_name)

    def create_version(self,project, release_name):
        self.jira.create_version(release_name,project)


