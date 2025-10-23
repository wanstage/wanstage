module.exports = {
  apps: [
    {
      name: "wan-ui-dev",
      script: "bash",
      args: ["-lc", "source $HOME/WANSTAGE/.venv/bin/activate && streamlit run $HOME/WANSTAGE/ui_main.py --server.port=${WAN_DEV_PORT:-8502} --server.headless=true"],
      env: { "WAN_DEV_PORT": process.env.WAN_DEV_PORT || "8502" },
      autorestart: true,
      max_memory_restart: "512M"
    }
  ]
}
