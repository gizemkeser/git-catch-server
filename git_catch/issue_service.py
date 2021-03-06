import requests
from string import Template
from decouple import config
from issue_catcher.models import Label, User


def get_issues():
    url = 'https://api.github.com/graphql'
    headers = {'Authorization': f'token {config("GITHUB_API_TOKEN")}'}

    query_template = Template(
        """
        {
          search(first: 100, type: ISSUE, query: "state:open is:public label:$label created:2019-01-18T15:00..2019-01-18T19:00") {
            edges {
              node {
                ... on Issue {
                  title
                  url
                  createdAt
                  repository {
                    name
                    url
                    languages(first:10) {
                      edges {
                        node {
                          name
                        }
                      }
                    }
                  }
                  labels(first:10) {
                    edges {
                      node {
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }            
        """
    )

    issue_list = []
    for label in Label.objects.all():
        response = requests.post(url=url, json={'query': query_template.substitute(label=label.name)}, headers=headers)
        json_res = response.json()
        issue_list.extend([item['node'] for item in json_res['data']['search']['edges'] if item['node']])

    return issue_list


def filter_issues():
    issue_list = get_issues()
    users = User.objects.all()
    for user in users:
        user_labels = user.labels.values_list('name', flat=True)
        user_languages = user.languages.values_list('name', flat=True)
        users_issues = [
            issue for issue in issue_list
            for label in issue['labels']['edges']
            for language in issue['repository']['languages']['edges']
            if label['node']['name'] in user_labels and language['node']['name'] in user_languages
        ]
