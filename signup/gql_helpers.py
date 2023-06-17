import signup.graphql_client as gclc 

client = gclc.Client("http://localhost:1337/graphql")

def clear_source():
    for j in client.all_jobs().jobs.data:
        print("Delete job:", j.id)
        client.delete_job(int(j.id))

    for r in client.all_roles().staffroles.data:
        print("Delete role", r.id)
        client.delete_role(int(r.id))

    for s in client.all_sources().sources.data:
        print("Delete source", s.id)
        client.delete_source(int(s.id))

if __name__ == '__main__':
    #clear_source()
    pass