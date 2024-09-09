#  * - = - = - =
#  * spec file for package YTCON
#  * - = - = - =
#  * Copyright (C) 2023-2024 Nikita Beloglazov <nnikita.beloglazov@gmail.com>
#  *
#  * This file is part of github.com/NikitaBeloglazov/ytcon.
#  *
#  * NikitaBeloglazov/ytcon is free software; you can redistribute it and/or
#  * modify it under the terms of the Mozilla Public License 2.0
#  * published by the Mozilla Foundation.
#  *
#  * NikitaBeloglazov/ytcon is distributed in the hope that it will be useful,
#  * but WITHOUT ANY WARRANTY.
#  *
#  * You should have received a copy of the Mozilla Public License 2.0
#  * along with NikitaBeloglazov/ytcon
#  * If not, see https://mozilla.org/en-US/MPL/2.0.
#  * - = - = - =
#  * Please submit bugfixes or comments via https://github.com/NikitaBeloglazov/ytcon/issues
#  * - = - = - =

%define pythons python3
Name:           ytcon
# Version sets dynamically by _service
Version:        0.0.0
Release:        0
Summary:        yt-dlp pseudo-graphical console interface (TUI)
License:        MPL-2.0
URL:            https://github.com/NikitaBeloglazov/ytcon
Source0:        %{name}-%{version}.tar
BuildRequires:  python-rpm-macros
BuildRequires:  %{python_module setuptools}
BuildRequires:  %{python_module setuptools_scm}
BuildRequires:  %{python_module pip}
BuildRequires:  fdupes

Requires:       python3
Requires:       python3-requests
Requires:       python3-tqdm
Requires:       python3-urwid
Requires:       python3-clipman
Requires:       python3-ffmpeg-python
Requires:       ffmpeg
Requires:       python3-yt-dlp

BuildArch:      noarch

%description
yt-dlp pseudo-graphical console interface (TUI). More at https://github.com/NikitaBeloglazov/ytcon

%prep
echo "DEBUG - PREP RUNNING"
%autosetup -p1 -n ytcon-%{version}
# This is needed for the auto-update system, so that ytcon will know that this is an RPM and will refuse to auto-update.
export SOURCE_FILE_TEXT="__source__ = source = 'rpm'" # Because escaping quotes doesn't seem to work in RPM spec
bash -c 'echo $SOURCE_FILE_TEXT > src/ytcon/__source__.py'

%build
echo "DEBUG - BUILD RUNNING"
export SETUPTOOLS_SCM_PRETEND_VERSION="v%{version}"
%pyproject_wheel

%install
echo "DEBUG - INSTALL RUNNING"
%pyproject_install

%files
%{_bindir}/ytcon
%{python_sitelib}/ytcon
%{python_sitelib}/ytcon-%{version}.dist-info
%license LICENSE
%doc README.md

%changelog
