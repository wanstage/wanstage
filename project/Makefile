SHELL := /bin/zsh

run:
	@project/bin/task.zsh --input project/sample.txt --verbose | tee -a project/var/log/task.$(shell date -u +%F).log

logs:
	@tail -f project/var/log/task.*.log || true

clean:
	@rm -f project/var/log/*.log || true
