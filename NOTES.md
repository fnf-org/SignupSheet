# Notes for Strapi Backend Adoption 

These are my notes from my proof of concept implementation of the Staff Sheet using Strapi. 

## Current State 

The current code has the Staff Sheet schema implemented in Strapi. The application can:

1. Use the whole sheet editor to clear and load the Source/Role/Job parts 
1. Coordinators don't work for no reason 

### Next Steps 

The API access is ad-hoc so I could learn GraphQL. A better implementation would use generated code to make access less tedious. 

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