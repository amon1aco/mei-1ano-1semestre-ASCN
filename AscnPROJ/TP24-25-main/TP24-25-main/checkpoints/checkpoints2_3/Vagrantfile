# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.

#Variables
PUBLIC_KEY_PATH = "~/.ssh/id_rsa.pub" #Change me if needed!
PRIVATE_KEY_PATH = "~/.ssh/id_rsa"  #Change me if needed!
READ_PUBLIC_KEY = File.read(File.expand_path(PUBLIC_KEY_PATH)).strip

# TP VM
TP_VM_IP  = "192.168.56.50"   #Change me if needed!

Vagrant.configure("2") do |config|

  # Global configurations
  config.vm.box = "bento/ubuntu-24.04"
  config.vm.box_version = "202404.26.0"
  config.vm.provider "vmware_desktop" do |vb|
    vb.force_vmware_license = "workstation"
    vb.memory = 1024
    vb.cpus = 2
  end

  # TP VM configurations
  config.vm.define :tpvm do |tp|
    tp.vm.hostname = "tpvm"
    tp.vm.network :private_network, ip: TP_VM_IP
    tp.vm.provision :shell, privileged: true, inline: $provision
    tp.vm.provision :docker
    tp.vm.provision :file, source: "./checkpoints2_3.sh", destination: "~/checkpoints2_3.sh"
    tp.vm.provision :file, source: "../../codebase", destination: "~/codebase"
  end

end

# Provisioning script
$provision = <<-SHELL
  echo "[Task 1] Configure SSH Public Key authentication"
  echo "#{READ_PUBLIC_KEY}" >> /home/vagrant/.ssh/authorized_keys
  sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/g' /etc/ssh/sshd_config
  sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/g' /etc/ssh/sshd_config
  systemctl restart ssh.service

  echo "[Task 2] Update Package List"
  apt update -y

  echo "[Task 3] Install Curl"
  apt install -y curl

  echo "[Task 4] Install gh"
  type -p curl >/dev/null || (apt update && apt install curl -y)
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && sudo apt update 

  echo "[Task 5] Install Ansible"
  apt update
  apt install -y ansible
  
  echo "[Task 6] Install Python"
  apt install python3-pip -y
  apt install python3.12-venv -y
  python3 -m venv /home/vagrant/.checkpoints
  chown -R vagrant:vagrant /home/vagrant/.checkpoints
  echo "source /home/vagrant/.checkpoints/bin/activate" >> /home/vagrant/.bashrc
  apt install python3-kubernetes -y



SHELL
