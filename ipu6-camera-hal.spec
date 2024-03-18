%global commit da2e2821244f21b95bcb37a1271bf73360c4669e
%global commitdate 20240226
%global shortcommit %(c=%{commit}; echo ${c:0:7})

# We want to specify multiple separate build-dirs for the different variants
%global __cmake_in_source_build 1

Name:           ipu6-camera-hal
Summary:        Hardware abstraction layer for Intel IPU6
URL:            https://github.com/intel/ipu6-camera-hal
Version:        0.0
Release:        16.%{commitdate}git%{shortcommit}%{?dist}
License:        Apache-2.0

Source0:        https://github.com/intel/%{name}/archive/%{commit}/%{name}-%{shortcommit}.tar.gz
Source1:        60-intel-ipu6.rules
Source2:        v4l2-relayd-adl
Source3:        v4l2-relayd-tgl
Source4:        intel_ipu6_isys.conf

# Patches
Patch01:        0001-Patch-lib-path-to-align-fedora-path-usage.patch

BuildRequires:  systemd-rpm-macros
BuildRequires:  ipu6-camera-bins-devel
BuildRequires:  cmake
BuildRequires:  gcc
BuildRequires:  g++
BuildRequires:  expat-devel

ExclusiveArch:  x86_64

Requires:       ipu6-camera-bins

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
for i in ipu_tgl ipu_adl ipu_mtl; do
  export PKG_CONFIG_PATH=%{_libdir}/$i/pkgconfig/
  export LDFLAGS="$RPM_LD_FLAGS -Wl,-rpath=%{_libdir}/$i"
  sed -i.orig "s|/usr/share/defaults/etc/camera/|/usr/share/defaults/etc/$i/|g" \
    src/platformdata/PlatformData.h
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
         -DBUILD_CAMHAL_TESTS=OFF -DUSE_PG_LITE_PIPE=ON ..
  %make_build
  popd

  mkdir $i"_adaptor" && pushd $i"_adaptor"
  %cmake ../src/hal/hal_adaptor
  popd
  mv src/platformdata/PlatformData.h.orig src/platformdata/PlatformData.h
done


%install
for i in ipu_tgl ipu_adl ipu_mtl; do
  pushd $i
  %make_install
  mkdir %{buildroot}%{_libdir}/$i
  mv %{buildroot}%{_usr}/lib/libcamhal.so %{buildroot}%{_libdir}/$i/
  mv %{buildroot}%{_datadir}/defaults/etc/camera %{buildroot}%{_datadir}/defaults/etc/$i
  popd
  pushd $i"_adaptor"
  %make_install
  mv %{buildroot}%{_usr}/lib64/libhal_adaptor.so %{buildroot}%{_libdir}/$i/
  popd
done

# We don't want static libs
rm %{buildroot}%{_usr}/lib/libcamhal.a

# symbolic link + udev is used to resolve the library name conflict. 
ln -sf %{_rundir}/libcamhal.so %{buildroot}%{_libdir}/libcamhal.so
ln -sf %{_rundir}/libhal_adaptor.so %{buildroot}%{_libdir}/libhal_adaptor.so
install -p -m 0644 -D %{SOURCE1} %{buildroot}%{_udevrulesdir}/60-intel-ipu6.rules

# Make sure libcamhal.so can be found when building code on systems without an IPU6
sed -i -e "s|\${prefix}/lib|\${prefix}/lib64/ipu_tgl|g" %{buildroot}%{_libdir}/pkgconfig/libcamhal.pc
sed -i -e "s|\${prefix}/lib|\${prefix}/lib64/ipu_tgl|g" %{buildroot}%{_libdir}/pkgconfig/hal_adaptor.pc

# v4l2-relayd configuration examples
install -p -D -m 0644 %{SOURCE2} %{buildroot}%{_datadir}/defaults/etc/ipu6ep/v4l2-relayd
install -p -D -m 0644 %{SOURCE3} %{buildroot}%{_datadir}/defaults/etc/ipu6/v4l2-relayd

# Make kmod-intel-ipu6 use /dev/video7 leaving /dev/video0 for loopback
install -p -D -m 0644 %{SOURCE4} %{buildroot}%{_modprobedir}/intel_ipu6_isys.conf


%post
# skip triggering if udevd isn't even accessible, e.g. containers or
# rpm-ostree-based systems
if [ -S /run/udev/control ]; then
    /usr/bin/udevadm control --reload
    /usr/bin/udevadm trigger /sys/devices/pci0000:00/0000:00:05.0
fi


%files
%license LICENSE
%{_libdir}/*/libcamhal.so
%{_libdir}/*/libhal_adaptor.so
%{_libdir}/libcamhal.so
%{_libdir}/libhal_adaptor.so
%{_datadir}/defaults/etc/*
%{_modprobedir}/intel_ipu6_isys.conf
%{_udevrulesdir}/60-intel-ipu6.rules


%files devel
%{_includedir}/libcamhal
%{_includedir}/hal_adaptor
%{_libdir}/pkgconfig/libcamhal.pc
%{_libdir}/pkgconfig/hal_adaptor.pc


%changelog
* Tue Mar 12 2024 Kate Hsuan <hpa@redhat.com> - 0.0-17.20240226gitda2e282
- Update to the latest upstream commit
- Include a new library hal_adaptor.so

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
