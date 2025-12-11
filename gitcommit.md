
### (참고) 커밋 시간 조정 스크립트
정상 커밋은 `git commit`을 사용하고, 시간만 조정하고 싶을 때만 아래 함수를 쓰세요. 기본은 현재 시각보다 **-17시간**으로 기록합니다.
`~/.bashrc` 또는 `~/.zshrc`에 추가:
```bash
gitcommit() {
  local hours=-17   # 기본값: 17시간 전

  # 첫 번째 인자가 숫자이면 그것을 hours로 사용
  if [[ "$1" =~ ^-?[0-9]+$ ]]; then
    hours="$1"
    shift
  fi

  local d
  d=$(date -d "${hours} hours" -Iseconds)

  GIT_AUTHOR_DATE="$d" \
  GIT_COMMITTER_DATE="$d" \
  git commit "$@" --date="$d"
}
```
터미널 재시작 후 `gitcommit -m "메시지"`(기본 -17시간) 또는 `gcommit 2 -m "메시지"`처럼 호출해 Author/Committer 시간을 조정할 수 있습니다.

### 최근 커밋 변경
```bash
d=$(date -d "-22 hours" -Iseconds)
GIT_AUTHOR_DATE="$d" GIT_COMMITTER_DATE="$d" git commit --amend --no-edit --date="$d"
git show -s --format="AUTHOR_DATE   : %ai%nCOMMITTER_DATE: %ci" HEAD
```

### 시스템 Timezone 변경

~/.bashrc 또는 ~/.zshrc에 아래 한 줄을 추가하고 터미널을 다시 열면 됩니다:

export TZ=Asia/Seoul

확인 : date 입력

### git log 의 local 시간 출력

단일 명령어 : git log --date=local
글로벌 : git config --global log.date local