tmux has-session -t my_vpn 2>/dev/null || tmux new-session -d -s my_vpn

tmux a -t my_vpn-1

openvpn --auth-nocache --config ruangong3.ovpn