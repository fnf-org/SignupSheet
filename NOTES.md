# Notes for Strapi Backend Adoption 

These are my notes from my proof of concept implementation of the Staff Sheet using Strapi. 

## Current State 

The current code has the Staff Sheet schema partly implemented in Strapi. The application can:

1. Use the whole sheet editor to clear and load the Source/Role/Job/Coordinator parts 
1. Display a simplified job page 

This is probably as far as I'm going to take functionality. The GraphQL implementation is interesting 
because you can do so much work in a single query. The `clade` query loads an entire page worth of 
data to display. 

The generated code can be created by: 

```
rm -rf signup/graphql_client && ariadne-codegen client
``` 

The generated classes are pretty handy. They're made a bit less convenient by the Strapi schema which
has both content and metadata, increasing the depth of useful stuff. 

### Next Steps 

Build an authentication flow. 

## Issues 

### Authentication 

This seems possible but isn't tested yet. 

### Transactions 

Strapi supports database transactions on the server side. It does **not** support API-level transactions for obvious reasons. This means that apps can't simply be ported over to the new backend because the ORM transactions that Django and Rails rely on are not possible. 

The solution is to implement transactional components inside of Strapi and make them available as API endpoints. For the Staff Sheet that would require at least these custom endpoints:

1. `reload` -- Blank and reload the entire DB based on parsed input. 
1. `signup` -- Sign up a user for a job
1. `unsignup` -- Delete a user job 

This is a leaky abstraction, some of the core logic of an app has to be implemented on the server side. 

### File Storage 

If this is to be hosted in a cloud native way a cloud storage plugin is required. 