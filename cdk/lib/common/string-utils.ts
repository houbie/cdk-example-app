function snake(str: string): string {
    return str.replace(/(?<!^)(?=[A-Z])/g, '_').toLowerCase()
}


function kebab(str: string): string {
    return str.replace(/(?<!^)(?=[A-Z])/g, '-').toLowerCase()
}

function title(str: string): string {
    return str ? str[0].toUpperCase() + str.substring(1) : str
}


export {
    snake,
    kebab,
    title
}
