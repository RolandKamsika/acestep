On enki, `~/repos/ACE-Step-1.5/acestep.sh up` starts ACE-Step (it stops `llama-swap`, since both can't fit on the GPUs). `acestep.sh down` reverses it. Ready after about a minute; log in `~/repos/ACE-Step-1.5/gradio.log`.

A copy of the script is in this folder ([acestep.sh](acestep.sh)). The live one is on enki. After editing the copy here, push it back:

scp acestep.sh 192.168.50.205:repos/ACE-Step-1.5/

From Windows:

ssh 192.168.50.205 '~/repos/ACE-Step-1.5/acestep.sh up'
ssh 192.168.50.205 '~/repos/ACE-Step-1.5/acestep.sh down'

 http://192.168.50.205:7860
  http://enki.local:7860
