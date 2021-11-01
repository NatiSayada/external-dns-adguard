# external-dns-adguard
Just like external-dns but for AdGuard Home

## What is this

so i was playing around with my cluster and i needed to make some automation around internal dns.
I really like external-dns and start looking for something similar that will work with adguard home.
didn't find one.. so i decided to build something like that.

## Getting Started
Get the manifest file from ```/deploy/deployment.yaml``` and modify the environment variables as you need.
apply the manifest, checkout the the container log to see how it works.

```bash
kubectl apply -f deploy/deployment.yaml
```

this project is based on the work of [Pobek](https://github.com/Pobek/external-dns-pihole) that did a great job for making this work for pi-hole..
