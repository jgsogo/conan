{% extends 'base_toolchain.cmake' %}

{% block main %}
    {{ super() }}

    set(CONAN_CXX_FLAGS "${CONAN_CXX_FLAGS} /MP{{ tc.cpu_count }}")
    set(CONAN_C_FLAGS "${CONAN_C_FLAGS} /MP{{ tc.cpu_count }}")
{% endblock %}
