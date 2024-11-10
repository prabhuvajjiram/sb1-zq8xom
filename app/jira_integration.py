from atlassian import Jira
from loguru import logger
import os
from dotenv import load_dotenv

load_dotenv()

class JiraIntegration:
    def __init__(self):
        self.jira = Jira(
            url=os.getenv('JIRA_URL'),
            username=os.getenv('JIRA_USERNAME'),
            password=os.getenv('JIRA_API_TOKEN')
        )

    def get_project_issues(self, project_key: str):
        try:
            jql = f'project = {project_key}'
            issues = self.jira.jql(jql)
            return self._process_issues(issues)
        except Exception as e:
            logger.error(f"Error fetching Jira issues: {str(e)}")
            raise

    def _process_issues(self, issues):
        processed = []
        for issue in issues.get('issues', []):
            processed.append({
                'key': issue['key'],
                'summary': issue['fields']['summary'],
                'description': issue['fields'].get('description', ''),
                'status': issue['fields']['status']['name']
            })
        return processed