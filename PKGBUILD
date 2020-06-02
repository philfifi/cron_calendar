pkgname=cron_calendar
pkgrel=1
pkgver=r18.e627109
pkgdesc='Get events from google calendar and execute commands'
arch=('any')
license=('GPL2')
depends=('python'
         "python-google-api-python-client"
         "python-oauth2client"
         "python-httplib2"
         )
# md5sums=('SKIP')


prepare() {
          ln -snf "$startdir" "$srcdir/$pkgname"
}


pkgver() {
    printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

build() {
    cd "$pkgname"
    python setup.py build
}

package() {
    cd "$pkgname"
    python setup.py install --root="$pkgdir/" --optimize=1 --skip-build
}
