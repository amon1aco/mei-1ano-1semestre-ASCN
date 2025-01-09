#!/bin/bash

function clean_up {
    echo "> Cleaning resources..."
    kubectl get namespaces --no-headers | \
        grep -vE '^(default|kube-system|kube-public|gke-system|gke-managed-cim|gmp-system|gmp-public|kube-node-lease|gke-managed-system)' | \
        awk '{print $1}' | \
        xargs -I {} kubectl delete namespace {}
    kubectl delete all --all --namespace=default > /dev/null 2>&1
    kubectl delete pvc --all -A > /dev/null 2>&1
    kubectl delete sc --all --namespace=default > /dev/null 2>&1
}

clean_up