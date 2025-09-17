#!/bin/bash
# AWS 最安構成セットアップスクリプト

echo "🚀 AWS コスト最適化環境セットアップ開始"

# 1. t2.nano インスタンス起動 (最安)
aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --instance-type t2.nano \
    --key-name your-key-pair \
    --security-group-ids sg-xxxxxxxxx \
    --subnet-id subnet-xxxxxxxxx \
    --associate-public-ip-address \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=cost-optimized-clicker}]'

# 2. Elastic IP 割り当て (年額$43.80 = 月額$3.65)
aws ec2 allocate-address --domain vpc

# 3. システム更新 & Python設定
sudo yum update -y
sudo yum install -y python3 python3-pip git

# 4. 軽量パッケージインストール
pip3 install --user requests urllib3

# 5. スクリプトダウンロード
git clone https://github.com/your-repo/web-clicker-py.git
cd web-clicker-py

# 6. cron で定期実行設定 (24時間稼働)
echo "0 */6 * * * cd /home/ec2-user/web-clicker-py && python3 aws_cost_optimized.py" | crontab -

echo "✅ セットアップ完了"
echo "月額コスト: $8.70"
echo "処理能力: 57,600アクセス/日"
