FROM fedora:29

USER root

# installing essential packages
RUN dnf install -y git vim python python-devel python-pip ansible gnupg gnupg2 python-requests procps-ng && dnf clean all

# setup everything
ADD playbooks /playbooks

# prepare config file and
RUN ansible-playbook /playbooks/initial_setup.yml

CMD ansible-playbook /playbooks/run_prt.yml
