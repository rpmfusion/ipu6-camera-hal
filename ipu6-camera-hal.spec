%global commit 289e645dffbd0ea633f10bb4f93855f1e4429e9a
%global commitdate 20240509
%global shortcommit %(c=%{commit}; echo ${c:0:7})

# We want to specify multiple separate build-dirs for the different variants
%global __cmake_in_source_build 1

Name:           ipu6-camera-hal
Summary:        Hardware abstraction layer for Intel IPU6
URL:            https://github.com/intel/ipu6-camera-hal
Version:        0.0
Release:        18.%{commitdate}git%{shortcommit}%{?dist}
License:        Apache-2.0

Source0:        https://github.com/intel/%{name}/archive/%{commit}/%{name}-%{shortcommit}.tar.gz
Source1:        60-intel-ipu6.rules
Source2:        v4l2-relayd-adl
Source3:        v4l2-relayd-tgl
Source4:        icamera_ipu6_isys.conf

# Patches
Patch01:        0001-Patch-lib-path-to-align-fedora-path-usage.patch
# https://github.com/intel/ipu6-camera-hal/pull/113
Patch02:        0001-CMakeLists-fixes.patch
# https://github.com/intel/ipu6-camera-hal/pull/114
Patch03:        0001-MediaControl-Dymically-set-mainline-IVSC-media-entit.patch

BuildRequires:  systemd-rpm-macros
BuildRequires:  ipu6-camera-bins-devel >= 0.0-11
BuildRequires:  cmake
BuildRequires:  gcc
BuildRequires:  g++
BuildRequires:  expat-devel
BuildRequires:  libdrm-devel

ExclusiveArch:  x86_64

Requires:       ipu6-camera-bins >= 0.0-11

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
sed -i "s|/etc/camera/|/usr/share/defaults/etc/camera/|g" \
  src/platformdata/PlatformData.h


%build
for i in ipu_tgl ipu_adl ipu_mtl; do
  export PKG_CONFIG_PATH=%{_libdir}/$i/pkgconfig/
  export LDFLAGS="$RPM_LD_FLAGS -Wl,-rpath=%{_libdir}/$i"
  mkdir $i && pushd $i
  if [ $i = "ipu_tgl" ]; then
    IPU_VERSION=ipu6
  elif [ $i = "ipu_adl" ]; then
    IPU_VERSION=ipu6ep
  elif [ $i = "ipu_mtl" ]; then
    IPU_VERSION=ipu6epmtl
  else
    IPU_VERSION=ipu
  fi
  %cmake -DCMAKE_BUILD_TYPE=Release -DIPU_VER=$IPU_VERSION \
         -DCMAKE_INSTALL_SUB_PATH:PATH="$i" \
         -DCMAKE_INSTALL_SYSCONFDIR:PATH="share/defaults/etc" \
         -DBUILD_CAMHAL_TESTS=OFF -DUSE_PG_LITE_PIPE=ON ..
  %make_build
  popd
done

# hal_adaptor.so dispatches between different libcamhal.so builds, only build it once
mkdir hal_adaptor && pushd hal_adaptor
%cmake ../src/hal/hal_adaptor
%make_build
popd


%install
for i in ipu_tgl ipu_adl ipu_mtl; do
  pushd $i
  %make_install
  rm %{buildroot}%{_libdir}/$i/libcamhal.a
  # new icamerasrc must use hal_adaptor, drop libcamhal.pc
  rm -r %{buildroot}%{_libdir}/$i/pkgconfig
  popd
done

pushd hal_adaptor
%make_install
popd

# udev-rules set the ipu_xxx /run/v4l2-relayd cfg link + /dev/ipu-psys0 uaccess
install -p -m 0644 -D %{SOURCE1} %{buildroot}%{_udevrulesdir}/60-intel-ipu6.rules

# v4l2-relayd configuration examples (mtl uses same config as adl)
install -p -m 0644 %{SOURCE2} %{buildroot}%{_datadir}/defaults/etc/camera/ipu_adl/v4l2-relayd
install -p -m 0644 %{SOURCE2} %{buildroot}%{_datadir}/defaults/etc/camera/ipu_mtl/v4l2-relayd
install -p -m 0644 %{SOURCE3} %{buildroot}%{_datadir}/defaults/etc/camera/ipu_tgl/v4l2-relayd

# Make kmod-intel-ipu6 use /dev/video7 leaving /dev/video0 for loopback
install -p -D -m 0644 %{SOURCE4} %{buildroot}%{_modprobedir}/icamera_ipu6_isys.conf


%post
# skip triggering if udevd isn't even accessible, e.g. containers or
# rpm-ostree-based systems
if [ -S /run/udev/control ]; then
    /usr/bin/udevadm control --reload
    /usr/bin/udevadm trigger /sys/devices/pci0000:00/0000:00:05.0
fi


%files
%license LICENSE
# per variant libcamhal.so links are also in main pkg because libhal_adaptor opens them
%{_libdir}/*/libcamhal.so*
%{_libdir}/libhal_adaptor.so.*
%{_datadir}/defaults
%{_modprobedir}/icamera_ipu6_isys.conf
%{_udevrulesdir}/60-intel-ipu6.rules


%files devel
%{_includedir}/hal_adaptor
%{_libdir}/libhal_adaptor.so
%{_libdir}/pkgconfig/hal_adaptor.pc


%changelog
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
