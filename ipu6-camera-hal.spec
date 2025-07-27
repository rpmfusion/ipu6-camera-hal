%global commit b6f6eeb68f06cd0d4a2463b8950847b1b98cebaa
%global commitdate 20241218
%global shortcommit %(c=%{commit}; echo ${c:0:7})

Name:           ipu6-camera-hal
Summary:        Hardware abstraction layer for Intel IPU6
URL:            https://github.com/intel/ipu6-camera-hal
Version:        0.0
Release:        25.%{commitdate}git%{shortcommit}%{?dist}
License:        Apache-2.0

Patch1:         0001-Drop-Werror.patch

Source0:        https://github.com/intel/%{name}/archive/%{commit}/%{name}-%{shortcommit}.tar.gz
Source1:        60-intel-ipu6.rules
Source2:        v4l2-relayd-tgl
Source3:        v4l2-relayd-adl
Source4:        ipu6-driver-select.sh

BuildRequires:  systemd-rpm-macros
BuildRequires:  ipu6-camera-bins-devel >= 0.0-16
BuildRequires:  cmake
BuildRequires:  gcc
BuildRequires:  g++
BuildRequires:  expat-devel
BuildRequires:  libdrm-devel

ExclusiveArch:  x86_64

Requires:       ipu6-camera-bins >= 0.0-16

%description
ipu6-camera-hal provides the basic hardware access APIs for IPU6.

%package devel
Summary:        IPU6 header files for HAL
Requires:       %{name}%{?_isa} = %{version}-%{release}
Requires:       ipu6-camera-bins-devel

%description devel
This provides the necessary header files for IPU6 HAL development.

%prep
%autosetup -p1 -n %{name}-%{commit}


%build
%cmake -DCMAKE_BUILD_TYPE=Release \
       -DCMAKE_INSTALL_SYSCONFDIR:PATH="%{_datadir}/defaults/etc" \
       -DBUILD_CAMHAL_ADAPTOR=ON \
       -DBUILD_CAMHAL_PLUGIN=ON \
       -DIPU_VERSIONS="ipu6;ipu6ep;ipu6epmtl" \
       -DUSE_PG_LITE_PIPE=ON
%cmake_build


%install
%cmake_install
# Drop the static plugin libs, only the .so files are actually used
rm %{buildroot}%{_libdir}/libcamhal/plugins/*.a

# udev-rules set the ipu_xxx /run/v4l2-relayd cfg link + /dev/ipu-psys0 uaccess
install -p -m 0644 -D %{SOURCE1} %{buildroot}%{_udevrulesdir}/60-intel-ipu6.rules

# v4l2-relayd configuration examples (adl and mtl use the same config)
install -p -m 0644 %{SOURCE2} %{buildroot}%{_datadir}/defaults/etc/camera/ipu6/v4l2-relayd
install -p -m 0644 %{SOURCE3} %{buildroot}%{_datadir}/defaults/etc/camera/ipu6ep/v4l2-relayd
install -p -m 0644 %{SOURCE3} %{buildroot}%{_datadir}/defaults/etc/camera/ipu6epmtl/v4l2-relayd

# Script to switch between proprietary and foss ipu6 stacks
install -p -D -m 0755 %{SOURCE4} %{buildroot}%{_bindir}/ipu6-driver-select


%posttrans
# skip triggering if udevd isn't even accessible, e.g. containers or
# rpm-ostree-based systems
if [ -S /run/udev/control ]; then
    /usr/bin/udevadm control --reload
    /usr/bin/udevadm trigger /sys/devices/pci0000:00/0000:00:05.0
fi


%files
%license LICENSE
%{_bindir}/ipu6-driver-select
%{_libdir}/libcamhal.so.*
%{_libdir}/libcamhal
%{_datadir}/defaults
%{_udevrulesdir}/60-intel-ipu6.rules

%files devel
%{_includedir}/libcamhal
%{_libdir}/libcamhal.so
%{_libdir}/pkgconfig/libcamhal.pc


%changelog
* Sun Jul 27 2025 RPM Fusion Release Engineering <sergiomb@rpmfusion.org> - 0.0-25.20241218gitb6f6eeb
- Rebuilt for https://fedoraproject.org/wiki/Fedora_43_Mass_Rebuild

* Sun Feb  2 2025 Hans de Goede <hdegoede@redhat.com> - 0.0-24.20241218gitb6f6eeb
- Drop /etc/modprobe.d/ipu6-driver-select.conf since the out of tree
  ISP driver and the mainline CSI receiver driver can now co-exist

* Fri Jan 31 2025 Hans de Goede <hdegoede@redhat.com> - 0.0-23.20241218gitb6f6eeb
- Update to upstream commit b6f6eeb68f06cd0d4a2463b8950847b1b98cebaa

* Wed Jan 29 2025 RPM Fusion Release Engineering <sergiomb@rpmfusion.org> - 0.0-22.20240509git289e645
- Rebuilt for https://fedoraproject.org/wiki/Fedora_42_Mass_Rebuild

* Tue Oct 15 2024 Hans de Goede <hdegoede@redhat.com> - 0.0-21.20240509git289e645
- %%ghost /etc/modprobe.d/ipu6-driver-select.conf

* Fri Aug 02 2024 RPM Fusion Release Engineering <sergiomb@rpmfusion.org> - 0.0-20.20240509git289e645
- Rebuilt for https://fedoraproject.org/wiki/Fedora_41_Mass_Rebuild

* Wed Jul  3 2024 Hans de Goede <hdegoede@redhat.com> - 0.0-19.20240509git289e645
- Add ipu6-driver-select script to switch between proprietary and foss stacks

* Mon Jun 24 2024 Hans de Goede <hdegoede@redhat.com> - 0.0-18.20240509git289e645
- Update to commit 289e645dffbd0ea633f10bb4f93855f1e4429e9a
- Update /lib/modprobe.d/intel_ipu6_isys.conf for the out of tree module
  being renamed to icamera_ipu6_isys
- Adjust things for the libraries now having a proper .so.0 soname
- hal_adaptor.so dispatches between different libcamhal.so builds, only build it once
- New icamerasrc must use hal_adaptor, drop libcamhal files from -devel
- Fix ownership of /usr/share/defaults and /usr/share/defaults/etc

* Tue Mar 12 2024 Kate Hsuan <hpa@redhat.com> - 0.0-17.20230208git884b81a
- Update to the latest upstream commit
- Include a new library hal_adaptor.so

* Sun Feb 04 2024 RPM Fusion Release Engineering <sergiomb@rpmfusion.org> - 0.0-17.20230208git884b81a
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Tue Oct 10 2023 Hans de Goede <hdegoede@redhat.com> - 0.0-16.20230208git884b81a
- Update /lib/modprobe.d/intel_ipu6_isys.conf for newer versions of
  intel-ipu6-kmod creating up to 8 /dev/video# nodes

* Tue Aug 08 2023 Kate Hsuan <hpa@redhat.com> - 0.0-15.20230208git884b81a
- Updated to commit 884b81aae0ea19a974eb8ccdaeef93038136bdd4

* Thu Aug 03 2023 RPM Fusion Release Engineering <sergiomb@rpmfusion.org> - 0.0-14.20221112gitcc0b859
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild

* Thu Jun  8 2023 Hans de Goede <hdegoede@redhat.com> - 0.0-13.20221112gitcc0b859
- Add Raptor Lake IPU6EP PCI-id to 60-intel-ipu6.rules

* Tue May 30 2023 Kate Hsuan <hpa@redhat.com> - 0.0-12.20221112gitcc0b859
- Fix 11 and skip udev command for container and rpm-ostree environments

* Mon May 29 2023 Kate Hsuan <hpa@redhat.com> - 0.0-11.20221112gitcc0b859
- Add a sysfs path check for rpm-ostree since udev is unable to access in a container

* Mon May 15 2023 Hans de Goede <hdegoede@redhat.com> - 0.0-10.20221112gitcc0b859
- Add intel_ipu6_isys.conf to make ipu6-driver not clobber /dev/video0

* Mon May 08 2023 Kate Hsuan <hpa@redhat.com> - 0.0-9.20221112gitcc0b859
- Fix settings for Tiger lake CPU

* Wed Mar 22 2023 Kate Hsuan <hpa@redhat.com> - 0.0-8.20221112gitcc0b859
- Included v4l2-relayd configuration examples

* Mon Mar 20 2023 Kate Hsuan <hpa@redhat.com> - 0.0-7.20221112gitcc0b859
- udev rules for supporting v4l2-relayd

* Wed Feb 15 2023 Kate Hsuan <hpa@redhat.com> - 0.0-6.20221112gitcc0b859
- Allow ordinary users to access the camera

* Fri Feb 3 2023 Kate Hsuan <hpa@redhat.com> - 0.0-5.20221112gitcc0b859
- Patch path settings for the configuration files
- Remove udev workaround
- Fix rpmlint warnings

* Tue Jan 31 2023 Kate Hsuan <hpa@redhat.com> - 0.0-4.20221112gitcc0b859
- Remove udev scripts and the simplified rules are used
- Fix and patch gcc13 compile issues

* Tue Jan 17 2023 Kate Hsuan <hpa@redhat.com> - 0.0-3.20221112gitcc0b859
- Add symbolic link for camera configuration files

* Fri Nov 25 2022 Kate Hsuan <hpa@redhat.com> - 0.0-2.20221112gitcc0b859
- push udev rules
- format and style fixes

* Fri Nov 25 2022 Kate Hsuan <hpa@redhat.com> - 0.0-1.20221112gitcc0b859
- First commit
