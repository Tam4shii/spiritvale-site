/**
 * register-commands.ts — one-time script to register slash commands globally.
 *
 * Run once after deploy:
 *   DISCORD_APP_ID=<id> DISCORD_BOT_TOKEN=<token> npm run register
 */

const APP_ID = process.env.DISCORD_APP_ID;
const TOKEN  = process.env.DISCORD_BOT_TOKEN;

if (!APP_ID || !TOKEN) {
  console.error('Set DISCORD_APP_ID and DISCORD_BOT_TOKEN environment variables.');
  process.exit(1);
}

const commands = [
  {
    name: 'latest',
    description: 'Show the latest SpiritVale patch',
  },
  {
    name: 'patch',
    description: 'Show a specific patch by version number',
    options: [{ name: 'version', description: 'e.g. 0.18.0', type: 3, required: true }],
  },
  {
    name: 'status',
    description: 'Data freshness / patch monitor health',
  },
];

const res = await fetch(`https://discord.com/api/v10/applications/${APP_ID}/commands`, {
  method: 'PUT',
  headers: { Authorization: `Bot ${TOKEN}`, 'Content-Type': 'application/json' },
  body: JSON.stringify(commands),
});

const json = await res.json();
if (!res.ok) {
  console.error('Failed to register commands:', json);
  process.exit(1);
}
console.log(`Registered ${(json as any[]).length} slash command(s).`);
