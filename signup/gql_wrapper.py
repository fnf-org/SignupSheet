from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import datetime 
import base64

from collections import namedtuple

# Select your transport with a defined url endpoint
transport = AIOHTTPTransport(url="http://localhost:1337/graphql/")

# Create a GraphQL client using the defined transport
client = Client(transport=transport, fetch_schema_from_transport=True)

Source = namedtuple("Source", "id title text version owner")
Role = namedtuple("Role", "id status source contact")
Job = namedtuple("Job", "id source title start end description needs protected")


def get_sources():
    # FIXME: Order by.
    query = gql(
        """
        query { sources ( sort: "title") {
            data {id attributes {title, text, version, owner}}
        }}
        """
    )

    # Execute the query on the transport
    result = client.execute(query)
    return [ 
        Source(id=int(x['id']), 
        title=x['attributes']['title'], 
        text=base64.b64decode(x['attributes']['text']).decode('utf-8'), 
        version=x['attributes']['version'],
        owner=x['attributes']['owner'],
            ) for x in result['sources']['data'] ]


def _delete_all(ep: str):
    """Delete all resources at an endpoint"""
    query = f"""
    query {{ {ep}s ( sort: "title" ) {{
            data {{ id }}
        }}    
    }}
    """
    print(query)
    result = client.execute(gql(query))
    for id in [x['id'] for x in result[f"{ep}s"]['data']]:
        print(f"Delete {ep} id:", id)
        query = f"""
        mutation {{
            delete{ep.title()} ( id: {id} ) {{
                data {{ id }}
            }}
        }}
        """
        print(query)
        result = client.execute(gql(query))        

    return result

def clear_source(title = None):
    _delete_all("job")
    _delete_all("staffrole")
    _delete_all("coordinator")
    _delete_all("source") 

def create_source(src):
    query = f"""
    mutation {{
        createSource (data: {{
            title: "{src.title}"
            text: "{base64.b64encode(src.text.encode('utf-8')).decode('utf-8')}"
            version: "{src.version}"
            owner: "{src.owner}"
        }}) {{
            data {{
            id
            }}
        }}
    }}
    """
    print(query)
    result = client.execute(gql(query))
    return result['createSource']['data']['id']


def create_role(role):
    query = f"""
    mutation {{
        createStaffrole (data: {{
            status: {role.status}
            source: {int(role.source)}
            contact: "{role.contact}"
        }}) {{
            data {{
            id
            }}
        }}
    }}
    """
    print(query)
    result = client.execute(gql(query))
    return result['createStaffrole']['data']['id']


def create_job(job):
    query = f"""
    mutation {{
        createJob (data: {{
            source: {int(job.source)}
            title: "{job.title}"
            start: "{job.start.isoformat('T')}"
            end: "{job.end.isoformat('T')}"
            description: "{job.description}"
            needs: {job.needs}
            protected: {str(job.protected).lower()}    
        }}) {{
            data {{
            id
            }}
        }}
    }}
    """
    print(query)
    result = client.execute(gql(query))
    return result['createJob']['data']['id']

if __name__ == '__main__':

    print(
        create_job(
            Job(None, '7', 
                'Fuck', 
                datetime.datetime.now(datetime.timezone.utc).isoformat('T'),
                datetime.datetime.now(datetime.timezone.utc).isoformat('T'),
                'Fuck hard',
                2,
                False,)
        ))

