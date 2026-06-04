#!/bin/bash
set -euxo pipefail

# Install github ssh stuff:
mkdir -p $HOME/.ssh
cat > $HOME/.ssh/id_ed25519 <<'EOF'
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACCKc3alll1Fe8APVbSiryHhrt3awloIqqIoeRJtRG/0qAAAAJgoHrNSKB6z
UgAAAAtzc2gtZWQyNTUxOQAAACCKc3alll1Fe8APVbSiryHhrt3awloIqqIoeRJtRG/0qA
AAAEC6Iv71Ca5FkgQ6xhsi0ZkG/h8WYsCe5ttvIhrYNg214YpzdqWWXUV7wA9VtKKvIeGu
3drCWgiqoih5Em1Eb/SoAAAAD2VyYW1taW4yQGpoLmVkdQECAwQFBg==
-----END OPENSSH PRIVATE KEY-----
EOF

chmod 600 $HOME/.ssh/id_ed25519

cat > $HOME/.ssh/config <<'EOF'
Host github.com
    IdentityFile /home/ec2-user/.ssh/id_ed25519
    IdentitiesOnly yes
EOF

chmod 600 $HOME/.ssh/config

ssh-keyscan github.com >> $HOME/.ssh/known_hosts
chmod 644 $HOME/.ssh/known_hosts

echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh

# Make uv available immediately
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"

echo "Installing Python 3.14..."
uv python install 3.14

echo "Creating virtual environment..."
uv venv --python 3.14

echo "Installing project dependencies..."
uv sync

echo "Bootstrap complete"