#!/usr/bin/python3

import asyncio
import os

import aiohttp

from github_stats import Stats


################################################################################
# Individual Image Generation Functions
################################################################################

async def generate_overview(s: Stats) -> None:
    """
    Generate an SVG badge with summary statistics
    :param s: Represents user's GitHub statistics
    """
    with open("templates/overview.svg", "r") as f:
        output = f.read()

    output = output.replace("{{ name }}", await s.name)
    output = output.replace("{{ stars }}", f"{await s.stargazers:,}")
    output = output.replace("{{ forks }}", f"{await s.forks:,}")
    output = output.replace("{{ contributions }}",
                            f"{await s.total_contributions:,}")
    additions, deletions = await s.lines_changed
    output = output.replace("{{ lines_changed }}", f"{additions + deletions:,}")
    output = output.replace("{{ views }}", f"{await s.views:,}")
    output = output.replace("{{ repos }}", f"{len(await s.repos):,}")

    os.makedirs("generated", exist_ok=True)
    with open("generated/overview.svg", "w") as f:
        f.write(output)


async def generate_languages(s: Stats) -> None:
    """
    Generate an SVG badge with summary languages used
    :param s: Represents user's GitHub statistics
    """
    with open("templates/languages.svg", "r") as f:
        output = f.read()

    progress = ""
    lang_list = ""
    sorted_languages = sorted((await s.languages).items(), reverse=True,
                              key=lambda t: t[1].get("size"))
    delay_between = 150
    for i, (lang, data) in enumerate(sorted_languages):
        color = data.get("color")
        color = color if color is not None else "#000000"
        progress += (f'<span style="background-color: {color};'
                     f'width: {data.get("prop", 0):0.3f}%;" '
                     f'class="progress-item"></span>')
        lang_list += f"""
<li style="animation-delay: {i * delay_between}ms;">
<svg xmlns="http://www.w3.org/2000/svg" class="octicon" style="fill:{color};"
viewBox="0 0 16 16" version="1.1" width="16" height="16"><path
fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8z"></path></svg>
<span class="lang">{lang}</span>
<span class="percent">{data.get("prop", 0):0.2f}%</span>
</li>

"""

    output = output.replace("{{ progress }}", progress)
    output = output.replace("{{ lang_list }}", lang_list)

    os.makedirs("generated", exist_ok=True)
    with open("generated/languages.svg", "w") as f:
        f.write(output)


################################################################################
# Main Function
################################################################################

async def main() -> None:
    """
    Generate all badges
    """
    keys = ("ACCESS_TOKEN", "GITHUB_ACTOR", "EXCLUDED", "EXCLUDED_LANGS")
    settings = {key: os.getenv(key) for key in keys}

    # Fall back to config.yaml for any value not provided via the environment
    if os.path.exists("config.yaml"):
        import yaml
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
        if config:
            for key in keys:
                if not settings[key]:
                    settings[key] = config.get(key)

    access_token = settings["ACCESS_TOKEN"]
    user = settings["GITHUB_ACTOR"]
    exclude_repos_env = settings["EXCLUDED"]
    exclude_langs_env = settings["EXCLUDED_LANGS"]

    if not access_token:
        raise SystemExit(
            "A personal access token is required to proceed. Set the "
            "ACCESS_TOKEN environment variable or add ACCESS_TOKEN to config.yaml."
        )
    
    exclude_repos = None
    if exclude_repos_env:
        exclude_repos = {x.strip() for x in exclude_repos_env.split(",")}
        
    exclude_langs = None
    if exclude_langs_env:
        exclude_langs = {x.strip() for x in exclude_langs_env.split(",")}
        
    async with aiohttp.ClientSession() as session:
        s = Stats(user, access_token, session, exclude_repos=exclude_repos,
                  exclude_langs=exclude_langs)
        await asyncio.gather(generate_languages(s), generate_overview(s))


if __name__ == "__main__":
    asyncio.run(main())
