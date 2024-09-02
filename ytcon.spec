# TEST SPEC PLEASE DON'T LOOK INTO IT

%{?!python_module:%define python_module() python-%{**} python3-%{**}}
Name:           ytcon
Version:        0.0.0
Release:        0
Summary:        yt-dlp pseudo-graphical console interface (TUI)
License:        MIT
URL:            https://github.com/NikitaBeloglazov/ytcon
Source0:        *.tar
BuildRequires:  python-rpm-macros
BuildRequires:  %{python_module setuptools}
BuildRequires:  %{python_module hatchling}
BuildRequires:  %{python_module pip}
BuildRequires:    fdupes
Requires:         python3
BuildArch:      noarch
%python_subpackages

%description
# ShellGPT
yt-dlp pseudo-graphical console interface (TUI)

%prep
%autosetup -p1 -n ytcon-%{version}

%build
%pyproject_wheel

%install
%pyproject_install
%python_clone -a %{buildroot}%{_bindir}/ytcon
%python_expand %fdupes %{buildroot}%{$python_sitelib}

%post
%python_install_alternative ytcon

%postun
%python_uninstall_alternative ytcon

%files %{python_files}
%doc README.md README.md
%license LICENSE LICENSE
%python_alternative %{_bindir}/sgpt
%{python_sitelib}/ytcon
%{python_sitelib}/ytcon-%{version}.dist-info

%changelog
