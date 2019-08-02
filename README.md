# prt
PRT templates and other stuff to run PRT in openshift

2. deploy
1. add secret 
oc create secret generic credentials --from-file=.yaml_key --from-literal=TRACKERBOT_USER=admin \ 
                --from-literal=TRACKERBOT_TOKEN=blabla \
                --from-literal=GH_TOKEN=blabla \ 
                --from-literal=SPROUT_USER=dockerbot \
                --from-literal=SPROUT_PASSWORD=blabla \

oc adm policy add-scc-to-user anyuid -z prt
oc adm policy add-scc-to-user privileged -z prt