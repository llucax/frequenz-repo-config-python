# {{cookiecutter.title}}

## Introduction

{% raw -%}
{%
   include-markdown "../README.md"
   start="<!-- introduction -->"
   end="<!-- /introduction -->"
%}

## Supported Platforms

{%
   include-markdown "../README.md"
   start="<!-- supported-platforms -->"
   end="<!-- /supported-platforms -->"
%}
{% endraw -%}
