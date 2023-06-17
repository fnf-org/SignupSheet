import signup.graphql_client as gclc 

client = gclc.Client("http://localhost:1337/graphql")

def clear_source():
    for c in client.all_coordinators().coordinators.data:
        print("Delete coordinator:", c.id)
        client.delete_coordinator(int(c.id))

    for j in client.all_jobs().jobs.data:
        print("Delete job:", j.id)
        client.delete_job(int(j.id))

    for r in client.all_roles().staffroles.data:
        print("Delete role", r.id)
        client.delete_role(int(r.id))

    for s in client.all_sources().sources.data:
        print("Delete source", s.id)
        client.delete_source(int(s.id))

def clade(title):
    cl = client.get_clade(title)
    for c in cl.coordinators.data:
        print("Found coordinator:", c.attributes.name)
    for j in cl.jobs.data:
        print("Found job:", j.attributes.title)
    for r in cl.staffroles.data:
        print("Found role:", r.attributes.description)

if __name__ == '__main__':
    clade("Cafe Bruxia")
    pass
