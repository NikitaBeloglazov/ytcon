# TEST SPEC PLEASE DON'T LOOK INTO IT

%{?!python_module:%define python_module() python-%{**} python3-%{**}}
Name:           ytcon
Version:        0.0.0
Release:        0
Summary:        yt-dlp pseudo-graphical console interface (TUI)
License:        MPL-2.0
URL:            https://github.com/NikitaBeloglazov/ytcon
Source0:        %{name}-%{version}.tar
BuildRequires:  python-rpm-macros
BuildRequires:  %{python_module setuptools}
BuildRequires:  %{python_module setuptools_scm}
BuildRequires:  %{python_module hatchling}
BuildRequires:  %{python_module pip}
BuildRequires:  fdupes
BuildRequires:  git
Requires:       python3
BuildArch:      noarch
%python_subpackages

%description
yt-dlp pseudo-graphical console interface (TUI)

%prep
%autosetup -p1 -n ytcon-%{version}

%build
%pyproject_wheel

%install
%pyproject_install
%python_expand %fdupes %{buildroot}%{$python_sitelib}

%files %{python_files}
%{python_sitelib}/ytcon
%{python_sitelib}/ytcon-%{version}.dist-info

%changelog
