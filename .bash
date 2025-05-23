git commit --amend  # Remove a chave do .env e salve
git push --force   # Força a atualização no GitHub

git rebase -i HEAD~2  # Substitua "2" pelo número de commits a revisar
# Altere "pick" para "edit" no commit problemático, remova o segredo e faça:
git commit --amend
git rebase --continue
git push --force



